from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def create(self, *, email: str, hashed_password: str) -> User:
        values = {
            User.email: email,
            User.hashed_password: hashed_password,
        }
        statement = insert(User).values(values).returning(User)
        result = await self.session.scalar(statement)
        await self.session.commit()
        return result
