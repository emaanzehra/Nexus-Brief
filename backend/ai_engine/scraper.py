"""
NexusBrief — AI News Engine
=============================
Scrapes news articles for a given topic, summarises with Google Gemini 1.5 Flash,
and saves them directly to the database.

Can be run:
  • As a CLI:        python -m ai_engine.scraper --topic technology
  • From the fetch service (called by the scheduler)
  • Standalone:      python backend/ai_engine/scraper.py --topic technology --api-key KEY
"""

import argparse
import json
import sys
import time
import re
import random
import string
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

log = logging.getLogger("nexusbrief.ai_engine")

# ─── Mock corpus (used when FETCH_LIVE=False or no internet) ─────────────────

_MOCK_CORPUS: dict[str, list[dict]] = {
    "technology": [
        {
            "title": "OpenAI Announces GPT-5 with Breakthrough Reasoning Capabilities",
            "url": "https://techcrunch.com/2025/01/openai-gpt5",
            "source": "TechCrunch", "author": "Sarah Chen",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "content": (
                "OpenAI has officially unveiled GPT-5, its most powerful language model to date, "
                "featuring unprecedented reasoning capabilities that surpass human expert-level "
                "performance on a wide range of benchmarks. The model introduces a novel "
                "chain-of-thought architecture that breaks down complex problems into logical steps. "
                "CEO Sam Altman described it as 'a step change in AI capability'. Pricing has been "
                "reduced by 50% compared to GPT-4 Turbo, signalling major compute efficiency gains."
            ),
        },
        {
            "title": "Apple Vision Pro 2 Leaks Reveal Neural Interface and Carbon Frame",
            "url": "https://9to5mac.com/2025/01/vision-pro-2-leak",
            "source": "9to5Mac", "author": "Mark Gurman",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
            "content": (
                "Leaked CAD renders reveal Apple's Vision Pro 2 weighs just 280g, down from 600g, "
                "using a carbon fibre frame and M4 Ultra chip. A non-invasive neural interface reads "
                "subtle scalp electrical signals, allowing users to control visionOS through thought. "
                "The device features 8K MicroOLED displays at 120Hz. Launch expected late 2025 at $2,499."
            ),
        },
        {
            "title": "Nvidia Blackwell Ultra GPUs Shatter AI Training Records",
            "url": "https://theverge.com/2025/nvidia-blackwell-ultra",
            "source": "The Verge", "author": "Tom Warren",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
            "content": (
                "Nvidia announced the Blackwell Ultra architecture delivering 3× improvement over "
                "Hopper for LLM training. The B200 Ultra features 288GB HBM4 at 20TB/s bandwidth. "
                "NVLink 5.0 scales to 1,024 GPUs with near-linear performance. "
                "Enterprise pricing starts at $40,000 per unit; cloud availability Q2 2025."
            ),
        },
        {
            "title": "Stripe Launches AI Fraud Detection Preventing $1B in Annual Losses",
            "url": "https://stripe.com/blog/ai-fraud-detection-2025",
            "source": "Stripe Blog", "author": "Patrick Collison",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=18)).isoformat(),
            "content": (
                "Stripe's Radar 3.0 uses a custom LLM trained on billions of transactions to reduce "
                "fraud by 64% and false positives by 38%. The system analyses 4,000+ signals per "
                "transaction in real-time. Stripe estimates it prevents $1B annually in fraud. "
                "Available at no extra cost to all merchants globally within 30 days."
            ),
        },
        {
            "title": "Anthropic Releases Claude 4 with 92% SWE-Bench Pass Rate",
            "url": "https://anthropic.com/news/claude-4",
            "source": "Anthropic", "author": "Dario Amodei",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
            "content": (
                "Anthropic released Claude 4, achieving 92% on SWE-Bench, outperforming all prior "
                "models and human expert baselines. Extended thinking mode dramatically improves "
                "multi-step debugging. Available at $15 per million output tokens."
            ),
        },
    ],
    "finance": [
        {
            "title": "Federal Reserve Signals Three Rate Cuts in 2025 as Core Inflation Cools",
            "url": "https://wsj.com/fed-rate-cuts-2025",
            "source": "Wall Street Journal", "author": "Nick Timiraos",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            "content": (
                "Fed Chair Powell confirmed three 25bps cuts are on track for 2025. Core PCE "
                "inflation fell to 2.4%, inching toward the 2% target. Dot-plot projects rates "
                "ending 2025 at 3.75-4.0%. S&P 500 gained 1.8%, 10-year Treasury yield fell 15bps."
            ),
        },
        {
            "title": "Venture Capital in AI Reaches $120B in 2024, Up 3× Year-over-Year",
            "url": "https://bloomberg.com/ai-vc-2024",
            "source": "Bloomberg", "author": "Katie Roof",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat(),
            "content": (
                "Global VC investment in AI tripled to $120 billion in 2024. Analysts warn of "
                "concentration risk: 60% of capital flowed to just 12 companies. Late-stage "
                "valuations compressed 20% from 2023 peaks."
            ),
        },
    ],
    "science": [
        {
            "title": "Google DeepMind AlphaFold 3 Predicts Protein-Drug Binding at 80% Accuracy",
            "url": "https://wired.com/story/deepmind-alphafold-3",
            "source": "Wired", "author": "Emily Mullin",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
            "content": (
                "AlphaFold 3 models protein interactions with small molecules, DNA, and RNA "
                "simultaneously. It achieves 80% accuracy on blind benchmarks vs 50% for prior "
                "methods. Pfizer, Roche, and AstraZeneca announced drug discovery partnerships."
            ),
        },
    ],
    "world": [
        {
            "title": "International Climate Summit Reaches Landmark Carbon Reduction Agreement",
            "url": "https://bbc.com/news/climate-summit-2025",
            "source": "BBC News", "author": "Climate Desk",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
            "content": (
                "140+ nations signed a binding commitment to reduce carbon emissions 45% by 2035. "
                "Widely regarded as the most ambitious climate accord since Paris. Analysts say "
                "targets are achievable but require unprecedented clean energy investment."
            ),
        },
    ],
    "startups": [
        {
            "title": "Y Combinator Latest Cohort Raises Record Funding Before Demo Day",
            "url": "https://techcrunch.com/2025/yc-batch-record",
            "source": "TechCrunch", "author": "Connie Loizos",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=14)).isoformat(),
            "content": (
                "The latest YC batch attracted $800M+ pre-demo-day, the highest in YC's history. "
                "Intense competition for AI-native companies drove the record. Several startups "
                "already exceed $10M annualised revenue."
            ),
        },
    ],
    "health": [
        {
            "title": "New mRNA Vaccine Approach Shows 94% Efficacy Against Multiple Cancer Types",
            "url": "https://nature.com/articles/mrna-cancer-vaccine-2025",
            "source": "Nature Medicine", "author": "Research Team",
            "published_at": (datetime.now(timezone.utc) - timedelta(hours=20)).isoformat(),
            "content": (
                "A personalised mRNA vaccine platform has demonstrated 94% efficacy across "
                "multiple solid tumour types in Phase 2 trials. The approach trains the immune "
                "system against patient-specific tumour antigens. Phase 3 trials begin Q3 2025."
            ),
        },
    ],
}


def _get_mock_articles(topic: str, count: int) -> list[dict]:
    topic_lower = topic.lower()
    for key, articles in _MOCK_CORPUS.items():
        if key in topic_lower or topic_lower in key:
            return articles[:count]
    return _MOCK_CORPUS.get("technology", [])[:count]


def _scrape_live(topic: str, count: int) -> list[dict]:
    try:
        import requests
        import xml.etree.ElementTree as ET
        from datetime import datetime, timezone
        
        url = f"https://news.google.com/rss/search?q={topic.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        
        import re
        import html
        root = ET.fromstring(resp.text)
        items = []
        for item in root.findall('.//item')[:count]:
            title = item.findtext('title') or ""
            link = item.findtext('link') or ""
            pub_date = item.findtext('pubDate') or datetime.now(timezone.utc).isoformat()
            description = item.findtext('description') or title
            description = html.unescape(re.sub(r'<[^>]+>', ' ', description).strip())
            source = item.findtext('source') or "Unknown"
            
            items.append({
                "title": title,
                "url": link,
                "source": source,
                "author": source,
                "published_at": pub_date,
                "content": description,
            })
        return items if items else _get_mock_articles(topic, count)
    except Exception as e:
        log.warning("Live scraping failed (%s), falling back to mock corpus", e)
        return _get_mock_articles(topic, count)


def _summarise_with_gemini(article: dict, api_key: str, model: str = "gemini-2.5-flash") -> Optional[dict]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        gm = genai.GenerativeModel(model)

        prompt = f"""You are NexusBrief's editorial AI. Analyse the article and return ONLY valid JSON.
No markdown fences, no HTML tags, no backticks, no preamble. All text must be plain text.

ARTICLE TITLE: {article['title']}
ARTICLE CONTENT:
{article['content'][:4000]}

Return EXACTLY this JSON structure:
{{
  "title": "<refined headline, max 90 chars>",
  "ai_summary": "<2-3 sentence executive summary, professional, insight-driven>",
  "key_points": [
    "<first key takeaway, under 15 words>",
    "<second key takeaway, under 15 words>",
    "<third key takeaway, under 15 words>"
  ],
  "sentiment": "<MUST be exactly: positive | negative | neutral>",
  "reading_time": <integer 1-10>,
  "source_url": "{article['url']}",
  "source_name": "{article.get('source', 'Unknown')}",
  "author": "{article.get('author', '')}",
  "published_at": "{article.get('published_at', datetime.now(timezone.utc).isoformat())}",
  "is_featured": false
}}

RULES: Return ONLY the JSON object."""

        response = gm.generate_content(prompt)
        raw = response.text.strip()

        # Strip accidental markdown fences
        if "```" in raw:
            for part in raw.split("```"):
                part = part.strip().lstrip("json").strip()
                if part.startswith("{"):
                    raw = part
                    break

        result = json.loads(raw)

        # Sanitise
        result["key_points"] = result.get("key_points", [])[:3]
        result["reading_time"] = max(1, min(10, int(result.get("reading_time", 2))))
        s = str(result.get("sentiment", "neutral")).lower().strip()
        result["sentiment"] = s if s in ("positive", "negative", "neutral") else "neutral"
        return result

    except json.JSONDecodeError as e:
        log.error("JSON parse failed for '%s': %s", article['title'][:50], e)
        return _fallback_summary(article)
    except Exception as e:
        log.error("Gemini error for '%s': %s", article['title'][:50], e)
        return _fallback_summary(article)


def _fallback_summary(article: dict) -> dict:
    content = article.get("content", "")
    sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
    return {
        "title": article["title"][:90],
        "ai_summary": ". ".join(sentences[:2]) + "." if sentences else content[:200],
        "key_points": [
            f"Key development reported by {article.get('source', 'the press')}",
            "Further details available at the original source",
            "Industry impact and implications still being assessed",
        ],
        "sentiment": "neutral",
        "reading_time": max(1, len(content.split()) // 200),
        "source_url": article["url"],
        "source_name": article.get("source", "Unknown"),
        "author": article.get("author", ""),
        "published_at": article.get("published_at", datetime.now(timezone.utc).isoformat()),
        "is_featured": False,
    }


def _make_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80]
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{slug}-{suffix}"


# ─── Main fetch function (called by the fetch service) ───────────────────────

async def fetch_and_save(
    topic: str,
    category_slug: str,
    api_key: str,
    count: int = 5,
    live: bool = False,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Fetches articles for a topic, summarises with Gemini, saves to DB.
    Returns {"saved": N, "skipped": N, "errors": N}.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.database import AsyncSessionLocal
    from models.category import Category
    from models.article import Article
    from sqlalchemy import select

    raw_articles = _scrape_live(topic, count) if live else _get_mock_articles(topic, count)
    log.info("Topic '%s': %d raw articles loaded", topic, len(raw_articles))

    saved = skipped = errors = 0

    async with AsyncSessionLocal() as db:
        # Resolve or create category
        cat = (await db.execute(select(Category).where(Category.slug == category_slug))).scalar_one_or_none()
        if not cat:
            cat = Category(
                name=category_slug.title(),
                slug=category_slug,
                icon="📰", color="violet", dot_color="#8b5cf6", sort_order=99,
            )
            db.add(cat)
            await db.flush()

        for i, raw in enumerate(raw_articles, 1):
            log.info("  Summarising %d/%d: %s", i, len(raw_articles), raw["title"][:55])

            # Skip duplicates
            exists = (await db.execute(
                select(Article).where(Article.source_url == raw["url"])
            )).scalar_one_or_none()
            if exists:
                skipped += 1
                continue

            summary = _summarise_with_gemini(raw, api_key, model)
            if not summary:
                errors += 1
                continue

            try:
                key_points = summary.pop("key_points", [])
                pub_raw = summary.get("published_at")
                published_at = None
                if pub_raw:
                    try:
                        from dateutil import parser as dateparser
                        published_at = dateparser.parse(pub_raw)
                        if published_at and published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                    except Exception:
                        published_at = datetime.now(timezone.utc)

                art = Article(
                    category_id=cat.id,
                    title=summary.get("title", raw["title"])[:255],
                    slug=_make_slug(summary.get("title", raw["title"])),
                    ai_summary=summary.get("ai_summary", ""),
                    source_url=raw["url"][:2048],
                    source_name=summary.get("source_name", "Unknown")[:100],
                    author=summary.get("author", "")[:100],
                    image_url=summary.get("image_url"),
                    sentiment=summary.get("sentiment", "neutral"),
                    reading_time=max(1, min(30, int(summary.get("reading_time", 2)))),
                    is_featured=bool(summary.get("is_featured", False)),
                    is_published=True,
                    published_at=published_at or datetime.now(timezone.utc),
                )
                art.key_points = key_points
                db.add(art)
                await db.flush()
                saved += 1

            except Exception as e:
                log.warning("  Save error: %s", e)
                errors += 1

            if i < len(raw_articles):
                time.sleep(0.8)  # respect Gemini rate limits

        await db.commit()

    log.info("Topic '%s' complete — saved=%d skipped=%d errors=%d", topic, saved, skipped, errors)
    return {"saved": saved, "skipped": skipped, "errors": errors}


# ─── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    import os
    import sys

    # Allow running as: python backend/ai_engine/scraper.py --topic technology --api-key KEY
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

    parser = argparse.ArgumentParser(description="NexusBrief AI Scraper")
    parser.add_argument("--topic",    default="technology")
    parser.add_argument("--category", default="technology")
    parser.add_argument("--api-key",  default=os.environ.get("GEMINI_API_KEY", ""))
    parser.add_argument("--count",    type=int, default=5)
    parser.add_argument("--live",     action="store_true")
    args = parser.parse_args()

    if not args.api_key:
        print("[ERROR] GEMINI_API_KEY not set. Pass --api-key or set the env var.", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(fetch_and_save(
        topic=args.topic,
        category_slug=args.category,
        api_key=args.api_key,
        count=args.count,
        live=args.live,
    ))
    print(json.dumps(result, indent=2))
