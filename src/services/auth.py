from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import InvalidToken
from src.external.user_service import ExternalUserService, UserCreate
from src.logger import logger
from src.rabbit import Response, err
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.social_account import SocialAccountRepository
from src.repositories.user import UserRepository
from src.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, RevokeRequest, SoftDeleteRequest, TokenPair

from .password import PasswordHasher
from .token import TokenService


class AuthService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        social_accounts: SocialAccountRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        external_user_service: ExternalUserService,
    ):
        self.session = session
        self.users = users
        self.refresh_tokens = refresh_tokens
        self.social = social_accounts
        self.hasher = hasher
        self.tokens = tokens
        self.external_user_service = external_user_service

    async def issue_pair(self, user_id: UUID, family_id: UUID | None = None) -> TokenPair:
        family_id = family_id or uuid7()
        access, access_expires_at = self.tokens.create_access_token(user_id)
        refresh, jti, refresh_expires_at = self.tokens.create_refresh_token(user_id, family_id)
        await self.refresh_tokens.create(jti=jti, user_id=user_id, family_id=family_id, expires_at=refresh_expires_at)
        return TokenPair(access_token=access, refresh_token=refresh, expires_at=access_expires_at)

    async def register(self, request: RegisterRequest, correlation_id: str) -> Response[TokenPair]:
        if await self.users.get_by_email(request.email):
            return err(409, "Email already registered")

        user = await self.users.create(
            user_id=uuid7(),
            email=request.email,
            hashed_password=self.hasher.hash(request.password.get_secret_value()),
            commit=False,
        )

        user_created = await self.external_user_service.create_user(
            UserCreate(
                user_id=user.id,
                basic_role=request.basic_role,
                email=user.email,  # type: ignore
                nickname=request.nickname,
                timezone=request.timezone,
                locale=request.locale,
            ),
            correlation_id=correlation_id,
        )

        if user_created.status >= 300:
            return user_created

        await self.session.commit()
        return Response(data=await self.issue_pair(user.id))

    async def login(self, request: LoginRequest) -> Response[TokenPair]:
        email = request.email
        user = await self.users.get_by_email(email)
        if user is None:
            logger.debug(f"[AuthService] No such user with email {email}. Login failed")
            return err(401, "Invalid email or password")

        if user.hashed_password is None:
            logger.debug(f"[AuthService] User with email {email} has no hashed password. Login failed")
            return err(401, "Invalid email or password")

        if not self.hasher.verify(request.password.get_secret_value(), user.hashed_password):
            logger.debug(f"[AuthService] User with email {email} password check failed")
            return err(401, "Invalid email or password")

        if not user.is_active:
            return err(403, "User is inactive")
        return Response(data=await self.issue_pair(user.id))

    async def refresh(self, request: RefreshRequest) -> Response[TokenPair]:
        try:
            payload = self.tokens.decode_refresh(request.refresh_token)
        except InvalidToken as exc:
            return err(exc.status, exc.message)

        jti = UUID(payload["jti"])
        stored = await self.refresh_tokens.get(jti)
        if stored is None:
            logger.debug("[AuthService] There is no stored refresh token")
            return err(401, "Invalid or expired token")

        if stored.revoked:
            await self.refresh_tokens.revoke_family(stored.family_id)
            return err(401, "Refresh token reuse detected; session revoked")

        if stored.expires_at <= datetime.now(UTC):
            logger.debug("[AuthService] Token expired")
            return err(401, "Invalid or expired token")

        access, access_expires_at = self.tokens.create_access_token(stored.user_id)
        new_refresh, new_jti, refresh_expires_at = self.tokens.create_refresh_token(stored.user_id, stored.family_id)
        await self.refresh_tokens.create(
            jti=new_jti,
            user_id=stored.user_id,
            family_id=stored.family_id,
            expires_at=refresh_expires_at,
        )
        await self.refresh_tokens.revoke(stored.jti, replaced_by=new_jti)

        pair = TokenPair(
            access_token=access,
            refresh_token=new_refresh,
            expires_at=access_expires_at,
        )
        return Response(data=pair)

    async def revoke(self, request: RevokeRequest) -> Response:
        try:
            payload = self.tokens.decode_refresh(request.refresh_token)
        except InvalidToken:
            return Response(message="Token revoked")

        jti = UUID(payload["jti"])
        stored = await self.refresh_tokens.get(jti)
        if stored is None:
            return Response(message="Token revoked")

        if request.all_sessions:
            await self.refresh_tokens.revoke_all_for_user(stored.user_id)
        else:
            await self.refresh_tokens.revoke_family(stored.family_id)
        return Response(message="Token revoked")

    async def soft_delete_user(self, request: SoftDeleteRequest) -> Response:
        await self.users.soft_delete_user(request.user_id)
        await self.refresh_tokens.revoke_all_for_user(request.user_id)

        return Response()
