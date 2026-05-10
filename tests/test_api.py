"""
NexusBrief — Test Suite
========================
Run with:  pytest tests/ -v
"""

import pytest
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Override DB to use in-memory SQLite for tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY",   "test-secret-key")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

from main import app
from core.database import Base, get_db


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield session_factory
    await engine.dispose()


@pytest.fixture
async def client(test_db):
    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Seed on first use
    async with test_db() as db:
        from services.seed import seed_all
        await seed_all(db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Categories ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_categories(client):
    res = await client.get("/api/v1/categories")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    cat = data[0]
    assert "slug" in cat
    assert "name" in cat
    assert "dot_color" in cat
    assert "article_count" in cat


# ─── Articles ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_articles(client):
    res = await client.get("/api/v1/articles")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_articles_filter_category(client):
    res = await client.get("/api/v1/articles?category=technology")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["category"]["slug"] == "technology"


@pytest.mark.asyncio
async def test_list_articles_filter_sentiment(client):
    res = await client.get("/api/v1/articles?sentiment=positive")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["sentiment"] == "positive"


@pytest.mark.asyncio
async def test_list_articles_search(client):
    res = await client.get("/api/v1/articles?search=AI")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_article(client):
    # First get any article id
    res = await client.get("/api/v1/articles?per_page=1")
    assert res.status_code == 200
    items = res.json()["items"]
    if not items:
        pytest.skip("No articles seeded")
    article_id = items[0]["id"]

    res2 = await client.get(f"/api/v1/articles/{article_id}")
    assert res2.status_code == 200
    data = res2.json()
    assert data["id"] == article_id
    assert "ai_summary" in data
    assert "key_points" in data
    assert isinstance(data["key_points"], list)


@pytest.mark.asyncio
async def test_get_article_not_found(client):
    res = await client.get("/api/v1/articles/99999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_featured_articles(client):
    res = await client.get("/api/v1/articles/featured")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ─── Stats ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stats(client):
    res = await client.get("/api/v1/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_articles" in data
    assert "today_articles" in data
    assert "positive_articles" in data
    assert "total_sources" in data
    assert data["total_articles"] >= 0


# ─── Auth ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signup(client):
    res = await client.post("/api/v1/auth/signup", json={
        "first_name": "Test",
        "last_name":  "User",
        "email":      "test@nexusbrief.io",
        "password":   "securepassword123",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user_name"] == "Test User"
    assert data["user_email"] == "test@nexusbrief.io"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client):
    payload = {"first_name":"Dup","last_name":"User","email":"dup@nexusbrief.io","password":"password123"}
    await client.post("/api/v1/auth/signup", json=payload)
    res = await client.post("/api/v1/auth/signup", json=payload)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    # Sign up first
    await client.post("/api/v1/auth/signup", json={
        "first_name":"Login","last_name":"Test","email":"login@nexusbrief.io","password":"mypassword99"
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": "login@nexusbrief.io",
        "password": "mypassword99",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user_email"] == "login@nexusbrief.io"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    res = await client.post("/api/v1/auth/login", json={
        "email": "login@nexusbrief.io",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client):
    # Sign up + login to get token
    await client.post("/api/v1/auth/signup", json={
        "first_name":"Me","last_name":"Test","email":"me@nexusbrief.io","password":"password123"
    })
    login = await client.post("/api/v1/auth/login", json={
        "email":"me@nexusbrief.io","password":"password123"
    })
    token = login.json()["access_token"]
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@nexusbrief.io"


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


# ─── Contact ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_contact_submit(client):
    res = await client.post("/api/v1/contact", json={
        "name":       "Emaan Test",
        "email":      "emaan@company.com",
        "department": "support",
        "subject":    "Test message",
        "message":    "This is a test message from the test suite.",
    })
    assert res.status_code == 200
    assert res.json()["success"] is True


@pytest.mark.asyncio
async def test_contact_invalid(client):
    res = await client.post("/api/v1/contact", json={
        "name": "",
        "email": "not-an-email",
        "department": "",
        "subject": "",
        "message": "hi",
    })
    assert res.status_code == 422  # Pydantic validation error


# ─── Pagination ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pagination(client):
    res = await client.get("/api/v1/articles?per_page=2&page=1")
    assert res.status_code == 200
    data = res.json()
    assert data["per_page"] == 2
    assert len(data["items"]) <= 2
    assert "pages" in data


@pytest.mark.asyncio
async def test_invalid_per_page(client):
    res = await client.get("/api/v1/articles?per_page=999")
    assert res.status_code == 422
