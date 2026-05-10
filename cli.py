"""
NexusBrief — CLI Management Tool
===================================
Replaces `php artisan` commands.

Usage:
  python cli.py fetch --all                 # Fetch all configured topics
  python cli.py fetch --topic technology    # Fetch one topic
  python cli.py seed                        # Seed demo data
  python cli.py serve                       # Start dev server
  python cli.py prune                       # Remove old articles
"""

import asyncio
import sys
import os
import argparse
import logging

# ── Make sure `backend/` is on the path when running from project root ───────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger("nexusbrief.cli")


# ─── fetch ────────────────────────────────────────────────────────────────────

async def cmd_fetch(args):
    from core.config import settings
    from core.database import init_db
    from ai_engine.scraper import fetch_and_save

    await init_db()

    api_key = args.api_key or settings.GEMINI_API_KEY
    if not api_key:
        log.error("GEMINI_API_KEY is not set. Add it to .env or pass --api-key.")
        sys.exit(1)

    if args.all:
        topics = settings.TOPICS
        log.info("Fetching %d topic(s)…", len(topics))
        total_saved = total_skipped = 0
        for cfg in topics:
            r = await fetch_and_save(
                topic=cfg["topic"],
                category_slug=cfg["category"],
                api_key=api_key,
                count=args.count or settings.ARTICLES_PER_FETCH,
                live=args.live if args.live is not None else settings.FETCH_LIVE,
            )
            total_saved   += r["saved"]
            total_skipped += r["skipped"]
        log.info("✅  All topics done — saved=%d skipped=%d", total_saved, total_skipped)
    else:
        r = await fetch_and_save(
            topic=args.topic,
            category_slug=args.category,
            api_key=api_key,
            count=args.count or settings.ARTICLES_PER_FETCH,
            live=args.live if args.live is not None else settings.FETCH_LIVE,
        )
        log.info("✅  saved=%d skipped=%d errors=%d", r["saved"], r["skipped"], r["errors"])


# ─── seed ─────────────────────────────────────────────────────────────────────

async def cmd_seed(_args):
    from core.database import init_db, AsyncSessionLocal
    from services.seed import seed_all
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_all(db)
    log.info("✅  Seed complete")


# ─── prune ────────────────────────────────────────────────────────────────────

async def cmd_prune(args):
    from core.database import init_db, AsyncSessionLocal
    from core.config import settings
    from models.article import Article
    from sqlalchemy import delete
    from datetime import datetime, timedelta, timezone

    await init_db()
    days = args.days or settings.MAX_ARTICLE_AGE_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(Article).where(Article.published_at < cutoff)
        )
        await db.commit()
        log.info("✅  Pruned %d articles older than %d days", result.rowcount, days)


# ─── serve ────────────────────────────────────────────────────────────────────

def cmd_serve(args):
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


# ─── Argument parser ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="nexusbrief", description="NexusBrief CLI")
    sub = parser.add_subparsers(dest="command")

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch & summarise news articles")
    p_fetch.add_argument("--all",      action="store_true",     help="Fetch all configured topics")
    p_fetch.add_argument("--topic",    default="technology",    help="News topic")
    p_fetch.add_argument("--category", default="technology",    help="Category slug")
    p_fetch.add_argument("--api-key",  default="",              help="Gemini API key (overrides .env)")
    p_fetch.add_argument("--count",    type=int, default=None,  help="Articles per topic")
    p_fetch.add_argument("--live",     action="store_true", default=None,    help="Use live RSS scraping")

    # seed
    sub.add_parser("seed", help="Seed database with demo data")

    # prune
    p_prune = sub.add_parser("prune", help="Delete old articles")
    p_prune.add_argument("--days", type=int, default=None)

    # serve
    p_serve = sub.add_parser("serve", help="Start the FastAPI development server")
    p_serve.add_argument("--host",   default="127.0.0.1")
    p_serve.add_argument("--port",   type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true", default=True)

    args = parser.parse_args()

    if args.command == "fetch":
        asyncio.run(cmd_fetch(args))
    elif args.command == "seed":
        asyncio.run(cmd_seed(args))
    elif args.command == "prune":
        asyncio.run(cmd_prune(args))
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
