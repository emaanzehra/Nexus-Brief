"""NexusBrief — Categories Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from core.schemas import CategoryOut
from models.category import Category
from models.article import Article

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    stmt = select(Category).order_by(Category.sort_order, Category.name)
    result = await db.execute(stmt)
    cats = result.scalars().all()

    # Count published articles per category
    count_stmt = (
        select(Article.category_id, func.count(Article.id).label("cnt"))
        .where(Article.is_published == True)  # noqa
        .group_by(Article.category_id)
    )
    count_result = await db.execute(count_stmt)
    counts = {row.category_id: row.cnt for row in count_result}

    out = []
    for c in cats:
        out.append(CategoryOut(
            id=c.id,
            name=c.name,
            slug=c.slug,
            icon=c.icon,
            color=c.color,
            dot_color=c.dot_color,
            description=c.description,
            article_count=counts.get(c.id, 0),
        ))
    return out
