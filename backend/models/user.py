"""NexusBrief — User model"""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id:               Mapped[int]      = mapped_column(primary_key=True, index=True)
    name:             Mapped[str]      = mapped_column(String(150), nullable=False)
    email:            Mapped[str]      = mapped_column(String(255), unique=True, index=True)
    hashed_password:  Mapped[str]      = mapped_column(String(255), nullable=False)
    is_active:        Mapped[bool]     = mapped_column(Boolean, default=True)
    plan:             Mapped[str]      = mapped_column(String(20), default="free")
    created_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                        default=lambda: datetime.now(timezone.utc))
