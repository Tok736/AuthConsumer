import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.base_schemas import Response, err
from src.exceptions import InvalidToken
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.social_account import SocialAccountRepository
from src.repositories.user import UserRepository
from src.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RevokeRequest,
    TokenPair,
)

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
    ):
        self.session = session
        self.users = users
        self.refresh_tokens = refresh_tokens
        self.social = social_accounts
        self.hasher = hasher
        self.tokens = tokens

    async def issue_pair(self, user_id: int, family_id: uuid.UUID | None = None) -> TokenPair:
        family_id = family_id or uuid.uuid4()
        access, access_expires_at = self.tokens.create_access_token(user_id)
        refresh, jti, refresh_expires_at = self.tokens.create_refresh_token(user_id, family_id)
        await self.refresh_tokens.create(jti=jti, user_id=user_id, family_id=family_id, expires_at=refresh_expires_at)
        return TokenPair(access_token=access, refresh_token=refresh, expires_at=access_expires_at)

    async def register(self, request: RegisterRequest) -> Response[TokenPair]:
        if await self.users.get_by_email(request.email):
            return err(409, "Email already registered")

        user = await self.users.create(
            email=request.email,
            hashed_password=self.hasher.hash(request.password.get_secret_value()),
        )

        return Response(data=await self.issue_pair(user.id))

    async def login(self, request: LoginRequest) -> Response[TokenPair]:
        user = await self.users.get_by_email(request.email)
        if (
            user is None
            or user.hashed_password is None
            or not self.hasher.verify(request.password.get_secret_value(), user.hashed_password)
        ):
            return err(401, "Invalid email or password")
        if not user.is_active:
            return err(403, "User is inactive")
        return Response(data=await self.issue_pair(user.id))

    async def refresh(self, req: RefreshRequest) -> Response[TokenPair]:
        try:
            payload = self.tokens.decode_refresh(req.refresh_token)
        except InvalidToken as exc:
            return err(exc.status, exc.message)

        jti = uuid.UUID(payload["jti"])
        stored = await self.refresh_tokens.get(jti)
        if stored is None:
            return err(401, "Invalid or expired token")

        if stored.revoked:
            await self.refresh_tokens.revoke_family(stored.family_id)
            return err(401, "Refresh token reuse detected; session revoked")

        if stored.expires_at <= datetime.now(UTC):
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

    async def revoke(self, req: RevokeRequest) -> Response:
        try:
            payload = self.tokens.decode_refresh(req.refresh_token)
        except InvalidToken:
            return Response(message="Token revoked")

        jti = uuid.UUID(payload["jti"])
        stored = await self.refresh_tokens.get(jti)
        if stored is None:
            return Response(message="Token revoked")

        if req.all_sessions:
            await self.refresh_tokens.revoke_all_for_user(stored.user_id)
        else:
            await self.refresh_tokens.revoke_family(stored.family_id)
        return Response(message="Token revoked")
