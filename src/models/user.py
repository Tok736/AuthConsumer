from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, func, true
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


# fmt: off
class User(Base):
    __tablename__ = "user"

    id:              Mapped[UUID]            = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    email:           Mapped[str | None]      = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str | None]      = mapped_column(String(255))
    is_active:       Mapped[bool]            = mapped_column(server_default=true())
    deleted_at:      Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
# fmt: on
