import uuid
from datetime import datetime

from sqlalchemy import insert, select, update

from src.base_repository import BaseRepository
from src.models.refresh_token import RefreshToken


class RefreshTokenRepository(BaseRepository):
    async def get(self, jti: uuid.UUID) -> RefreshToken | None:
        return await self.session.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    async def create(
        self,
        *,
        jti: uuid.UUID,
        user_id: int,
        family_id: uuid.UUID,
        expires_at: datetime,
    ) -> RefreshToken:
        values = {
            RefreshToken.jti: jti,
            RefreshToken.user_id: user_id,
            RefreshToken.family_id: family_id,
            RefreshToken.expires_at: expires_at,
        }
        statement = insert(RefreshToken).values(values).returning(RefreshToken)
        return await self.session.scalar(statement)

    async def revoke(self, jti: uuid.UUID, replaced_by: uuid.UUID | None = None) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True, replaced_by=replaced_by)
        )

    async def revoke_family(self, family_id: uuid.UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
