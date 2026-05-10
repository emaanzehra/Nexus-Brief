"""
NexusBrief — Configuration
============================
All settings are loaded from environment variables (or .env file).
Sensible defaults allow zero-config local development with SQLite.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "NexusBrief"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"

    # ── Database ──────────────────────────────────────────────────────────────
    # SQLite by default (zero install).  Switch to PostgreSQL for production:
    #   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/nexusbrief
    DATABASE_URL: str = "sqlite+aiosqlite:///./nexusbrief.db"

    # ── AI / Gemini ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── News fetch ────────────────────────────────────────────────────────────
    ARTICLES_PER_FETCH: int = 5
    MAX_ARTICLE_AGE_DAYS: int = 30
    FETCH_LIVE: bool = True   # True = real RSS scraping; False = mock corpus

    # Topics fetched by `python -m cli fetch --all`
    TOPICS: List[dict] = [
        {"topic": "technology AI machine learning", "category": "technology"},
        {"topic": "finance stock market economy",   "category": "finance"},
        {"topic": "science research discovery",     "category": "science"},
        {"topic": "world politics international",   "category": "world"},
        {"topic": "startups venture capital SaaS",  "category": "startups"},
        {"topic": "health medicine biotech",        "category": "health"},
    ]

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:5500"]

    # ── Auth (simple JWT) ─────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days


settings = Settings()
