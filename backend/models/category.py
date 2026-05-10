"""NexusBrief — Category model"""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    name:        Mapped[str]      = mapped_column(String(100), nullable=False)
    slug:        Mapped[str]      = mapped_column(String(100), unique=True, index=True, nullable=False)
    icon:        Mapped[str]      = mapped_column(String(10), default="📰")
    color:       Mapped[str]      = mapped_column(String(30), default="violet")
    dot_color:   Mapped[str]      = mapped_column(String(10), default="#8b5cf6")
    description: Mapped[str|None] = mapped_column(String(500), nullable=True)
    sort_order:  Mapped[int]      = mapped_column(Integer, default=0)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   default=lambda: datetime.now(timezone.utc))
    updated_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   default=lambda: datetime.now(timezone.utc),
                                                   onupdate=lambda: datetime.now(timezone.utc))

    # relationship
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="category",  # noqa
                                                      lazy="dynamic")

    @property
    def article_count(self) -> int:
        return self.articles.filter_by(is_published=True).count()  # type: ignore
