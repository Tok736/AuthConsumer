"""Business logic for authentication.

Every mutating handler goes through ``_execute``, which implements the
idempotency guard and the single commit point:

    1. If the correlation_id was already processed -> return the cached reply.
    2. Otherwise run the action (which returns a Response envelope).
    3. Persist (idempotency row + any writes) and commit *before* replying.

Expected business outcomes (wrong password, email taken, token reuse, ...)
are returned as Response envelopes so their side effects are committed and
cached. Only truly unexpected errors bubble up, roll back, and let RabbitMQ
redeliver the message.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..exceptions import InvalidToken
from ..repositories.idempotency import IdempotencyRepository
from ..repositories.refresh_token import RefreshTokenRepository
from ..repositories.social_account import SocialAccountRepository
from ..repositories.user import UserRepository
from ..schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RevokeRequest,
    TokenPair,
    UserData,
)
from ..schemas.response import Response, err, ok
from .password import PasswordHasher
from .token import TokenService

Action = Callable[[], Awaitable[Response]]


class AuthService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        social_accounts: SocialAccountRepository,
        idempotency: IdempotencyRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        settings: Settings,
    ):
        self._session = session
        self._users = users
        self._refresh = refresh_tokens
        self._social = social_accounts
        self._idem = idempotency
        self._hasher = hasher
        self._tokens = tokens
        self._settings = settings

    # --- idempotency + commit wrapper ------------------------------------
    async def _execute(self, idem_key: str | None, action: Action) -> Response:
        if idem_key:
            cached = await self._idem.get(idem_key)
            if cached is not None:
                return Response.model_validate(cached)

        response = await action()

        if idem_key:
            await self._idem.save(idem_key, response.model_dump(mode="json"))
        await self._session.commit()
        return response

    # --- helpers ----------------------------------------------------------
    async def _issue_pair(self, user_id: uuid.UUID, family_id: uuid.UUID | None = None) -> TokenPair:
        family_id = family_id or uuid.uuid4()
        access, expires_in = self._tokens.create_access_token(user_id)
        refresh, jti, expires_at = self._tokens.create_refresh_token(user_id, family_id)
        await self._refresh.create(jti=jti, user_id=user_id, family_id=family_id, expires_at=expires_at)
        return TokenPair(access_token=access, refresh_token=refresh, expires_in=expires_in)

    # --- endpoints --------------------------------------------------------
    async def register(self, req: RegisterRequest, idem_key: str | None) -> Response:
        async def action() -> Response:
            if await self._users.get_by_email(req.email):
                return err(409, "Email already registered")
            user = await self._users.create(
                email=req.email,
                hashed_password=self._hasher.hash(req.password),
            )
            data = UserData(id=str(user.id), email=user.email, is_active=user.is_active)
            return ok(status=201, message="Created", data=data.model_dump())

        return await self._execute(idem_key, action)

    async def login(self, req: LoginRequest, idem_key: str | None) -> Response:
        async def action() -> Response:
            user = await self._users.get_by_email(req.email)
            # Same generic error whether the email or the password is wrong.
            if (
                user is None
                or user.hashed_password is None
                or not self._hasher.verify(req.password, user.hashed_password)
            ):
                return err(401, "Invalid email or password")
            if not user.is_active:
                return err(403, "User is inactive")
            pair = await self._issue_pair(user.id)
            return ok(data=pair.model_dump())

        return await self._execute(idem_key, action)

    async def refresh(self, req: RefreshRequest, idem_key: str | None) -> Response:
        async def action() -> Response:
            try:
                payload = self._tokens.decode_refresh(req.refresh_token)
            except InvalidToken as exc:
                return err(exc.status, exc.message)

            jti = uuid.UUID(payload["jti"])
            stored = await self._refresh.get(jti)
            if stored is None:
                return err(401, "Invalid or expired token")

            # Reuse of an already-rotated token => likely theft. Kill the
            # whole session (family), invalidating the attacker AND the
            # legitimate holder, who must re-authenticate.
            if stored.revoked:
                await self._refresh.revoke_family(stored.family_id)
                return err(401, "Refresh token reuse detected; session revoked")

            if stored.expires_at <= datetime.now(UTC):
                return err(401, "Invalid or expired token")

            # Rotate: mint a new pair in the same family, retire the old jti.
            access, expires_in = self._tokens.create_access_token(stored.user_id)
            new_refresh, new_jti, expires_at = self._tokens.create_refresh_token(stored.user_id, stored.family_id)
            await self._refresh.create(
                jti=new_jti,
                user_id=stored.user_id,
                family_id=stored.family_id,
                expires_at=expires_at,
            )
            await self._refresh.revoke(stored.jti, replaced_by=new_jti)

            pair = TokenPair(
                access_token=access,
                refresh_token=new_refresh,
                expires_in=expires_in,
            )
            return ok(data=pair.model_dump())

        return await self._execute(idem_key, action)

    async def revoke(self, req: RevokeRequest, idem_key: str | None) -> Response:
        async def action() -> Response:
            try:
                payload = self._tokens.decode_refresh(req.refresh_token)
            except InvalidToken:
                # Revoking an unknown/expired token is a harmless no-op.
                return ok(message="Token revoked")

            jti = uuid.UUID(payload["jti"])
            stored = await self._refresh.get(jti)
            if stored is None:
                return ok(message="Token revoked")

            if req.all_sessions:
                await self._refresh.revoke_all_for_user(stored.user_id)
            else:
                await self._refresh.revoke_family(stored.family_id)
            return ok(message="Token revoked")

        return await self._execute(idem_key, action)
