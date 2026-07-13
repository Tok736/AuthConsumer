from faststream import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.social_account import SocialAccountRepository
from src.repositories.user import UserRepository
from src.services import AuthService, get_password_hasher, get_token_service


def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(
        session=session,
        users=UserRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        social_accounts=SocialAccountRepository(session),
        hasher=get_password_hasher(),
        tokens=get_token_service(),
    )
