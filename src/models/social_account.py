from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


# fmt: off
class UserSocialAccount(Base):
    __tablename__ = "user_social_account"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_provider_identity"),)

    id:               Mapped[UUID]     = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id:          Mapped[UUID]     = mapped_column(PgUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), index=True)
    provider:         Mapped[str]      = mapped_column(String(50))
    provider_user_id: Mapped[str]      = mapped_column(String(255))
    created_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
# fmt: on
