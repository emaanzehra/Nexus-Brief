"""
NexusBrief — Background Scheduler
====================================
Runs inside the FastAPI process using APScheduler.
Replaces Laravel's `php artisan schedule:run` cron job.

Jobs:
  • Daily at 06:00 UTC  — fetch all topic news
  • Weekly on Sunday    — prune articles older than MAX_ARTICLE_AGE_DAYS
"""

import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

log = logging.getLogger("nexusbrief.scheduler")

scheduler = AsyncIOScheduler(timezone="UTC")


async def _fetch_all_topics():
    """Fetch and summarise news for every configured topic."""
    from core.config import settings
    from ai_engine.scraper import fetch_and_save

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        log.error("Scheduler: GEMINI_API_KEY not set — skipping fetch")
        return

    log.info("🗞  Scheduled fetch starting — %d topics", len(settings.TOPICS))
    total_saved = total_skipped = 0

    for cfg in settings.TOPICS:
        try:
            r = await fetch_and_save(
                topic=cfg["topic"],
                category_slug=cfg["category"],
                api_key=api_key,
                count=settings.ARTICLES_PER_FETCH,
                live=settings.FETCH_LIVE,
            )
            total_saved   += r["saved"]
            total_skipped += r["skipped"]
        except Exception as exc:
            log.error("Scheduler: topic '%s' failed — %s", cfg["topic"], exc)

    log.info("✅  Scheduled fetch done — saved=%d skipped=%d", total_saved, total_skipped)


async def _prune_old_articles():
    """Delete articles older than MAX_ARTICLE_AGE_DAYS."""
    from core.config import settings
    from core.database import AsyncSessionLocal
    from models.article import Article
    from sqlalchemy import delete

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.MAX_ARTICLE_AGE_DAYS)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(Article).where(Article.published_at < cutoff)
        )
        await db.commit()
        log.info("🧹  Pruned %d old articles (cutoff=%s)", result.rowcount, cutoff.date())


def start_scheduler():
    """Register all jobs and start the scheduler."""

    # Daily fetch at 06:00 UTC
    scheduler.add_job(
        _fetch_all_topics,
        trigger=CronTrigger(hour=6, minute=0),
        id="daily_fetch",
        name="Daily news fetch",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # Weekly prune on Sunday at 03:00 UTC
    scheduler.add_job(
        _prune_old_articles,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="weekly_prune",
        name="Weekly article prune",
        replace_existing=True,
    )

    scheduler.start()
    log.info("⏰  Scheduler started — next fetch at 06:00 UTC daily")
