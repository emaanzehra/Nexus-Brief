"""
NexusBrief — Articles Router
==============================
GET  /api/v1/articles          — paginated, filtered list
GET  /api/v1/articles/featured — top 3 featured articles
GET  /api/v1/articles/{id}     — single article
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from core.database import get_db
from core.schemas import ArticleOut, ArticleListOut
from models.article import Article
from models.category import Category

router = APIRouter(prefix="/articles", tags=["Articles"])


def _article_out(a: Article) -> ArticleOut:
    """Convert ORM object → Pydantic schema."""
    cat = None
    if a.category:
        from core.schemas import CategoryBrief
        cat = CategoryBrief(
            id=a.category.id,
            name=a.category.name,
            slug=a.category.slug,
            icon=a.category.icon,
            dot_color=a.category.dot_color,
        )
    return ArticleOut(
        id=a.id,
        title=a.title,
        slug=a.slug,
        ai_summary=a.ai_summary,
        key_points=a.key_points,
        source_url=a.source_url,
        source_name=a.source_name,
        author=a.author,
        image_url=a.image_url,
        sentiment=a.sentiment,
        sentiment_color=a.sentiment_color,
        reading_time=a.reading_time,
        reading_time_label=a.reading_time_label,
        is_featured=a.is_featured,
        time_ago=a.time_ago,
        published_at=a.published_at,
        category=cat,
        created_at=a.created_at,
    )


@router.get("", response_model=ArticleListOut)
async def list_articles(
    category:  Optional[str] = Query(None, description="Category slug"),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    search:    Optional[str] = Query(None, max_length=100),
    sort:      str           = Query("latest", pattern="^(latest|oldest|featured)$"),
    featured:  Optional[bool]= Query(None),
    page:      int           = Query(1, ge=1),
    per_page:  int           = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Article)
        .options(selectinload(Article.category))
        .join(Category, Article.category_id == Category.id)
        .where(Article.is_published == True)  # noqa
    )

    if category:
        stmt = stmt.where(Category.slug == category)
    if sentiment:
        stmt = stmt.where(Article.sentiment == sentiment)
    if featured is not None:
        stmt = stmt.where(Article.is_featured == featured)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Article.title.ilike(like),
                Article.ai_summary.ilike(like),
                Article.source_name.ilike(like),
            )
        )

    if sort == "oldest":
        stmt = stmt.order_by(Article.published_at.asc())
    elif sort == "featured":
        stmt = stmt.order_by(Article.is_featured.desc(), Article.published_at.desc())
    else:
        stmt = stmt.order_by(Article.published_at.desc())

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Paginate
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)
    result = await db.execute(stmt)
    articles = result.scalars().all()

    return ArticleListOut(
        items=[_article_out(a) for a in articles],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, -(-total // per_page)),
    )


@router.get("/featured", response_model=list[ArticleOut])
async def featured_articles(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Article)
        .options(selectinload(Article.category))
        .join(Category)
        .where(Article.is_published == True, Article.is_featured == True)  # noqa
        .order_by(Article.published_at.desc())
        .limit(3)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return [_article_out(a) for a in articles]


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Article)
        .options(selectinload(Article.category))
        .join(Category)
        .where(Article.id == article_id, Article.is_published == True)  # noqa
    )
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return _article_out(article)
