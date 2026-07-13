import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


# fmt: off
class RefreshToken(Base):
    __tablename__ = "refresh_token"

    jti:         Mapped[uuid.UUID]        = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:     Mapped[int]              = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    family_id:   Mapped[int]              = mapped_column(PgUUID(as_uuid=True), index=True)
    expires_at:  Mapped[datetime]         = mapped_column(DateTime(timezone=True))
    revoked:     Mapped[bool]             = mapped_column(Boolean, default=False, server_default="false", index=True)
    replaced_by: Mapped[uuid.UUID | None] = mapped_column()
    created_at:  Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:  Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
# fmt: on
