from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, select, update

from src.base_repository import BaseRepository
from src.models.user import User


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.scalar(select(User).where(User.id == user_id))

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def create(self, *, user_id: UUID, email: str, hashed_password: str, commit: bool = True) -> User:
        values = {
            User.id: user_id,
            User.email: email,
            User.hashed_password: hashed_password,
        }
        statement = insert(User).values(values).returning(User)
        user = await self.session.scalar(statement)
        if commit:
            await self.session.commit()
        return user

    async def soft_delete_user(self, user_id: UUID) -> None:
        values = {
            User.email: None,
            User.deleted_at: datetime.now(),
            User.is_active: False,
        }
        await self.session.execute(update(User).values(values).where(User.id == user_id))
