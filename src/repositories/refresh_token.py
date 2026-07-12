import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, jti: int) -> RefreshToken | None:
        return await self.session.get(RefreshToken, jti)

    async def create(
        self,
        *,
        jti: uuid.UUID,
        user_id: int,
        family_id: int,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            jti=jti,
            user_id=user_id,
            family_id=family_id,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def revoke(self, jti: int, replaced_by: int | None = None) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True, replaced_by=replaced_by)
        )

    async def revoke_family(self, family_id: int) -> None:
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
