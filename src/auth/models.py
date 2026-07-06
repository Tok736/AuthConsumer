from datetime import datetime

from sqlalchemy import DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


# fmt: off
class User(Base):
    __tablename__ = "user"

    id:              Mapped[int]        = mapped_column(primary_key=True)
    email:           Mapped[str]        = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    is_active:       Mapped[bool]       = mapped_column(server_default=true())
    created_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
# fmt: on
