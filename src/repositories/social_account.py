from sqlalchemy import insert, select

from src.base_repository import BaseRepository
from src.models.social_account import UserSocialAccount


class SocialAccountRepository(BaseRepository):
    async def get_by_provider(self, provider: str, provider_user_id: str) -> UserSocialAccount | None:
        statement = select(UserSocialAccount).where(
            UserSocialAccount.provider == provider,
            UserSocialAccount.provider_user_id == provider_user_id,
        )
        return await self.session.scalar(statement)

    async def create(self, *, user_id: int, provider: str, provider_user_id: str) -> UserSocialAccount:
        values = {
            UserSocialAccount.user_id: user_id,
            UserSocialAccount.provider: provider,
            UserSocialAccount.provider_user_id: provider_user_id,
        }
        statement = insert(UserSocialAccount).values(values).returning(UserSocialAccount)
        return await self.session.scalar(statement)
