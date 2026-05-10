"""
NexusBrief — Database
======================
Async SQLAlchemy 2.x with aiosqlite (local) or asyncpg (PostgreSQL).
The DATABASE_URL in config drives which engine is used — no code change needed.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from core.config import settings
import pathlib

# ─── Engine ──────────────────────────────────────────────────────────────────

_connect_args = {}
db_url = settings.DATABASE_URL

if db_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    # Force relative SQLite paths to resolve from the project root (nexusbrief) securely
    if "///./" in db_url:
        root_dir = pathlib.Path(__file__).resolve().parent.parent.parent
        db_url = db_url.replace("///./", f"///{root_dir.as_posix()}/")

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── Base model ───────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─── Dependency ───────────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# ─── Init ─────────────────────────────────────────────────────────────────────

async def init_db():
    """Create all tables and seed categories + demo articles if empty."""
    from models import category, article  # noqa — register models with Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default data
    async with AsyncSessionLocal() as db:
        from services.seed import seed_all
        await seed_all(db)
