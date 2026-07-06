"""FastStream dependency providers wiring sessions, repos and services."""

from functools import lru_cache

from faststream import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.idempotency import IdempotencyRepository
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.social_account import SocialAccountRepository
from src.repositories.user import UserRepository

from src.database import get_session
from src.services.auth import AuthService
from src.services.password import get_password_hasher
from src.services.token import TokenService


@lru_cache
def get_token_service() -> TokenService:
    """Singleton: RSA ключи загружаются один раз"""
    return TokenService()


def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(
        session=session,
        users=UserRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        social_accounts=SocialAccountRepository(session),
        idempotency=IdempotencyRepository(session),
        hasher=get_password_hasher(),
        tokens=get_token_service(),
        settings=get_settings(),
    )
