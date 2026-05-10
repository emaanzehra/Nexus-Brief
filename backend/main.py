"""
NexusBrief — FastAPI Backend
=============================
Single-process server that:
  • Serves the frontend SPA (index.html) at /
  • Exposes a versioned REST API at /api/v1/
  • Runs the AI news-fetch job via background tasks or CLI
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.database import init_db
from core.config import settings
from routers import articles, categories, stats, auth, contact
from services.scheduler import start_scheduler, scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
log = logging.getLogger("nexusbrief")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀  NexusBrief starting up — initialising database…")
    await init_db()
    log.info("✅  Database ready")
    start_scheduler()
    yield
    scheduler.shutdown()
    log.info("👋  NexusBrief shutting down")


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NexusBrief API",
    description="AI-powered news aggregation and summarisation platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routers ─────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(articles.router,   prefix=API_PREFIX)
app.include_router(categories.router, prefix=API_PREFIX)
app.include_router(stats.router,      prefix=API_PREFIX)
app.include_router(auth.router,       prefix=API_PREFIX)
app.include_router(contact.router,    prefix=API_PREFIX)

# ─── Static frontend (SPA) ───────────────────────────────────────────────────
# Serve the HTML file for every non-API route so browser history routing works.

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index = FRONTEND_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"error": "Frontend not found. Place index.html in frontend/"}

else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": "NexusBrief API is running",
            "docs": "/api/docs",
            "version": "1.0.0",
        }
