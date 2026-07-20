from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, select, update

from src.base_repository import BaseRepository
from src.models.refresh_token import RefreshToken


class RefreshTokenRepository(BaseRepository):
    async def get(self, jti: UUID) -> RefreshToken | None:
        return await self.session.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    async def create(
        self,
        *,
        jti: UUID,
        user_id: UUID,
        family_id: UUID,
        expires_at: datetime,
    ) -> RefreshToken:
        values = {
            RefreshToken.jti: jti,
            RefreshToken.user_id: user_id,
            RefreshToken.family_id: family_id,
            RefreshToken.expires_at: expires_at,
        }
        statement = insert(RefreshToken).values(values).returning(RefreshToken)
        refresh_token = await self.session.scalar(statement)
        await self.session.commit()
        return refresh_token

    async def revoke(self, jti: UUID, replaced_by: UUID | None = None) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True, replaced_by=replaced_by)
        )
        await self.session.commit()

    async def revoke_family(self, family_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.family_id == family_id, RefreshToken.revoked.is_(False)).values(revoked=True)
        )
        await self.session.commit()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)).values(revoked=True)
        )
        await self.session.commit()
