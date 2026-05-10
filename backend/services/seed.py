"""
NexusBrief — Seed Service
===========================
Inserts default categories and demo articles on first startup.
Idempotent: skips rows that already exist.
"""

from datetime import datetime, timedelta, timezone
import json
import re
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.category import Category
from models.article import Article


# ─── Default categories ───────────────────────────────────────────────────────

DEFAULT_CATEGORIES = [
    {"name": "Technology",  "slug": "technology",  "icon": "💻", "color": "violet",  "dot_color": "#8b5cf6", "sort_order": 1},
    {"name": "Finance",     "slug": "finance",     "icon": "💰", "color": "emerald", "dot_color": "#22d3a5", "sort_order": 2},
    {"name": "Science",     "slug": "science",     "icon": "🔬", "color": "blue",    "dot_color": "#60a5fa", "sort_order": 3},
    {"name": "World",       "slug": "world",       "icon": "🌍", "color": "amber",   "dot_color": "#f59e0b", "sort_order": 4},
    {"name": "Startups",    "slug": "startups",    "icon": "🚀", "color": "rose",    "dot_color": "#f43f5e", "sort_order": 5},
    {"name": "Health",      "slug": "health",      "icon": "🏥", "color": "teal",    "dot_color": "#14b8a6", "sort_order": 6},
]


# ─── Demo articles ─────────────────────────────────────────────────────────────

def _demo_articles(cat_map: dict[str, int]) -> list[dict]:
    now = datetime.now(timezone.utc)
    return [
        {
            "category_id":    cat_map["technology"],
            "title":          "OpenAI unveils its most capable model yet, surpassing expert benchmarks across key disciplines",
            "ai_summary":     "The company's latest model delivers a step-change in reasoning, outperforming human expert baselines on standardised tests for the first time. Productivity gains reported by early enterprise users have been described as transformational, particularly in knowledge work and complex analysis tasks.",
            "key_points":     ["Reasoning performance exceeds human expert level for the first time", "Enterprise users report 40–60% productivity gains in knowledge work", "Pricing reduced significantly, making it accessible to smaller teams"],
            "source_url":     "https://techcrunch.com/2025/01/openai-latest-model",
            "source_name":    "TechCrunch",
            "author":         "Sarah Chen",
            "sentiment":      "positive",
            "reading_time":   4,
            "is_featured":    True,
            "published_at":   now - timedelta(hours=2),
        },
        {
            "category_id":    cat_map["technology"],
            "title":          "Apple's next-generation headset leaks reveal dramatic weight reduction and hands-free control",
            "ai_summary":     "New documents show the forthcoming device weighs just 280g — less than half its predecessor — and introduces a control system that responds to subtle user intention, removing the need for physical gestures. Industry observers expect it to significantly widen the market.",
            "key_points":     ["Device weight cut by more than half, addressing top user complaint", "New control system requires no hand movements or voice commands", "Lower starting price expected to open the market to mainstream buyers"],
            "source_url":     "https://9to5mac.com/2025/01/vision-pro-2-leak",
            "source_name":    "9to5Mac",
            "author":         "Mark Gurman",
            "sentiment":      "positive",
            "reading_time":   3,
            "is_featured":    False,
            "published_at":   now - timedelta(hours=5),
        },
        {
            "category_id":    cat_map["finance"],
            "title":          "Central bank signals three interest rate reductions this year as inflation data improves",
            "ai_summary":     "The head of the central bank confirmed that conditions are in place for a gradual easing cycle, with core inflation now within striking distance of the 2% target. Financial markets responded with broad-based gains, with equities reaching multi-month highs on the announcement.",
            "key_points":     ["Three rate reductions now firmly on the agenda for the year ahead", "Inflation reading at lowest point since 2021, bolstering the case", "Equity markets rose sharply, bond yields fell across the curve"],
            "source_url":     "https://wsj.com/fed-rate-cuts-2025",
            "source_name":    "Wall Street Journal",
            "author":         "Nick Timiraos",
            "sentiment":      "positive",
            "reading_time":   5,
            "is_featured":    True,
            "published_at":   now - timedelta(hours=3),
        },
        {
            "category_id":    cat_map["technology"],
            "title":          "New data-centre hardware delivers three times the performance for AI workloads",
            "ai_summary":     "The latest generation of AI-optimised computing hardware triples throughput for the most demanding workloads, while major cloud providers have committed to making it available to customers within months. Analysts expect this to materially reduce costs for businesses running large-scale AI applications.",
            "key_points":     ["Three times faster processing for demanding AI applications", "Major cloud providers committed to availability within months", "Expected to reduce operating costs for AI-intensive businesses"],
            "source_url":     "https://theverge.com/2025/nvidia-blackwell-ultra",
            "source_name":    "The Verge",
            "author":         "Tom Warren",
            "sentiment":      "positive",
            "reading_time":   3,
            "is_featured":    False,
            "published_at":   now - timedelta(hours=12),
        },
        {
            "category_id":    cat_map["science"],
            "title":          "Scientific breakthrough cuts drug discovery timeline from years to weeks",
            "ai_summary":     "A landmark advance in computational biology now allows researchers to predict how drug molecules will interact with specific proteins with 80% accuracy — a figure that rivals costly and time-consuming laboratory experiments. The world's largest pharmaceutical companies have moved swiftly to incorporate the technology.",
            "key_points":     ["Prediction accuracy now rivals traditional lab experiments", "Drug development timelines could shrink from years to weeks", "Major pharmaceutical companies have already adopted the method"],
            "source_url":     "https://wired.com/story/deepmind-alphafold-3",
            "source_name":    "Wired",
            "author":         "Emily Mullin",
            "sentiment":      "positive",
            "reading_time":   6,
            "is_featured":    False,
            "published_at":   now - timedelta(hours=8),
        },
        {
            "category_id":    cat_map["finance"],
            "title":          "Investment in AI companies tripled last year, but capital is becoming more concentrated",
            "ai_summary":     "Total investment in AI-focused businesses reached $120 billion last year, triple the prior year's figure. However, analysts are flagging concentration risk, with the majority of capital flowing to a small number of established players rather than spreading across the wider ecosystem.",
            "key_points":     ["Total AI investment reached $120 billion, tripling year-on-year", "Most capital flowing to a handful of large, established firms", "Late-stage valuations showing signs of moderation from peak levels"],
            "source_url":     "https://bloomberg.com/ai-vc-2024",
            "source_name":    "Bloomberg",
            "author":         "Katie Roof",
            "sentiment":      "neutral",
            "reading_time":   5,
            "is_featured":    False,
            "published_at":   now - timedelta(hours=10),
        },
        {
            "category_id":    cat_map["world"],
            "title":          "International climate summit reaches landmark agreement on carbon reduction targets",
            "ai_summary":     "More than 140 nations have signed a binding commitment to reduce carbon emissions by 45% before 2035, widely regarded as the most ambitious climate accord since the Paris Agreement. Independent analysts say the targets are technically achievable but will require unprecedented levels of investment in clean energy infrastructure.",
            "key_points":     ["140+ nations commit to binding 45% emissions cut by 2035", "Described as the most significant climate deal in a decade", "Requires trillions in clean energy investment to meet targets"],
            "source_url":     "https://bbc.com/news/climate-summit-2025",
            "source_name":    "BBC News",
            "author":         "Climate Desk",
            "sentiment":      "positive",
            "reading_time":   4,
            "is_featured":    False,
            "published_at":   now - timedelta(hours=6),
        },
        {
            "category_id":    cat_map["startups"],
            "title":          "Y Combinator's latest cohort raises record funding before demo day",
            "ai_summary":     "The latest Y Combinator batch has attracted pre-demo-day investment totalling over $800 million, the highest figure in the accelerator's history, driven by intense competition for AI-native companies. Several startups in the cohort are already operating at annualised revenue above $10 million.",
            "key_points":     ["Record $800M+ raised before demo day, a YC first", "AI-native companies dominating investor interest", "Multiple startups already exceed $10M annualised revenue"],
            "source_url":     "https://techcrunch.com/2025/yc-batch-record",
            "source_name":    "TechCrunch",
            "author":         "Connie Loizos",
            "sentiment":      "positive",
            "reading_time":   3,
            "is_featured":    False,
            "published_at":   now - timedelta(hours=14),
        },
    ]


def _make_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80]
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{slug}-{suffix}"


async def seed_all(db: AsyncSession):
    # ── Categories ────────────────────────────────────────────────────────────
    cat_map: dict[str, int] = {}
    for data in DEFAULT_CATEGORIES:
        existing = (await db.execute(
            select(Category).where(Category.slug == data["slug"])
        )).scalar_one_or_none()
        if not existing:
            cat = Category(**data)
            db.add(cat)
            await db.flush()
            cat_map[data["slug"]] = cat.id
        else:
            cat_map[data["slug"]] = existing.id

    await db.commit()

    # Reload map from DB (handles case where all already existed)
    result = await db.execute(select(Category))
    for c in result.scalars().all():
        cat_map[c.slug] = c.id

    # ── Articles ──────────────────────────────────────────────────────────────
    article_count = (await db.execute(select(Article))).scalars().first()
    if article_count is not None:
        return  # already seeded

    for data in _demo_articles(cat_map):
        key_points = data.pop("key_points", [])
        art = Article(**data, slug=_make_slug(data["title"]))
        art.key_points = key_points
        db.add(art)

    await db.commit()
