from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.social_account import UserSocialAccount


class SocialAccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_provider(self, provider: str, provider_user_id: str) -> UserSocialAccount | None:
        result = await self.session.execute(
            select(UserSocialAccount).where(
                UserSocialAccount.provider == provider,
                UserSocialAccount.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, *, user_id: int, provider: str, provider_user_id: str) -> UserSocialAccount:
        account = UserSocialAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
        self.session.add(account)
        await self.session.flush()
        return account
