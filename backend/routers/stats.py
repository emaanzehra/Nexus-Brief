"""NexusBrief — Stats Router"""

from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from core.schemas import StatsOut
from models.article import Article
from models.category import Category

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    total   = (await db.execute(select(func.count(Article.id)).where(Article.is_published == True))).scalar_one()  # noqa
    today   = (await db.execute(select(func.count(Article.id)).where(Article.is_published == True, Article.published_at >= today_start))).scalar_one()  # noqa
    pos     = (await db.execute(select(func.count(Article.id)).where(Article.is_published == True, Article.sentiment == "positive"))).scalar_one()  # noqa
    neg     = (await db.execute(select(func.count(Article.id)).where(Article.is_published == True, Article.sentiment == "negative"))).scalar_one()  # noqa
    neu     = (await db.execute(select(func.count(Article.id)).where(Article.is_published == True, Article.sentiment == "neutral"))).scalar_one()  # noqa
    n_cats  = (await db.execute(select(func.count(Category.id)))).scalar_one()
    sources = (await db.execute(select(func.count(func.distinct(Article.source_name))).where(Article.is_published == True))).scalar_one()  # noqa
    last_up = (await db.execute(select(func.max(Article.created_at)).where(Article.is_published == True))).scalar_one()  # noqa

    return StatsOut(
        total_articles=total,
        today_articles=today,
        positive_articles=pos,
        negative_articles=neg,
        neutral_articles=neu,
        total_categories=n_cats,
        total_sources=sources,
        last_updated=last_up,
    )
