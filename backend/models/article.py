"""NexusBrief — Article model"""

from datetime import datetime, timezone
from typing import Optional
import json

from sqlalchemy import (
    String, Integer, Text, Boolean, DateTime,
    ForeignKey, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("source_url", name="uq_articles_source_url"),
    )

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    category_id:      Mapped[int]           = mapped_column(Integer, ForeignKey("categories.id",
                                                             ondelete="CASCADE"), index=True)
    title:            Mapped[str]           = mapped_column(String(255), nullable=False)
    slug:             Mapped[str]           = mapped_column(String(300), unique=True, index=True)
    ai_summary:       Mapped[str]           = mapped_column(Text, nullable=False, default="")
    _key_points:      Mapped[str]           = mapped_column("key_points", Text, default="[]")
    original_content: Mapped[str|None]      = mapped_column(Text, nullable=True)

    # Source
    source_url:       Mapped[str]           = mapped_column(String(2048), nullable=False)
    source_name:      Mapped[str|None]      = mapped_column(String(100), nullable=True)
    author:           Mapped[str|None]      = mapped_column(String(100), nullable=True)
    image_url:        Mapped[str|None]      = mapped_column(String(2048), nullable=True)

    # AI analysis
    sentiment:        Mapped[str]           = mapped_column(
                                                SAEnum("positive", "negative", "neutral",
                                                       name="sentiment_enum"),
                                                default="neutral")
    reading_time:     Mapped[int]           = mapped_column(Integer, default=2)
    relevance_score:  Mapped[int]           = mapped_column(Integer, default=5)

    # Flags
    is_featured:      Mapped[bool]          = mapped_column(Boolean, default=False)
    is_published:     Mapped[bool]          = mapped_column(Boolean, default=True)

    # Timestamps
    published_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),
                                                                   nullable=True, index=True)
    created_at:       Mapped[datetime]      = mapped_column(DateTime(timezone=True),
                                                             default=lambda: datetime.now(timezone.utc))
    updated_at:       Mapped[datetime]      = mapped_column(DateTime(timezone=True),
                                                             default=lambda: datetime.now(timezone.utc),
                                                             onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    category: Mapped["Category"] = relationship("Category", back_populates="articles")  # noqa

    # ── key_points property (stored as JSON string in SQLite) ─────────────────

    @property
    def key_points(self) -> list[str]:
        try:
            return json.loads(self._key_points or "[]")
        except Exception:
            return []

    @key_points.setter
    def key_points(self, value: list[str]):
        self._key_points = json.dumps(value or [])

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def sentiment_color(self) -> str:
        return {"positive": "emerald", "negative": "red"}.get(self.sentiment, "zinc")

    @property
    def reading_time_label(self) -> str:
        return f"{self.reading_time} min read"

    @property
    def time_ago(self) -> str:
        if not self.published_at:
            return "Just now"
        now = datetime.now(timezone.utc)
        pub = self.published_at
        if pub.tzinfo is None:
            from datetime import timezone as tz
            pub = pub.replace(tzinfo=tz.utc)
        diff = now - pub
        secs = int(diff.total_seconds())
        if secs < 60:      return "Just now"
        if secs < 3600:    return f"{secs // 60} min ago"
        if secs < 86400:   return f"{secs // 3600} hours ago"
        if secs < 604800:  return f"{secs // 86400} days ago"
        return pub.strftime("%b %d, %Y")
