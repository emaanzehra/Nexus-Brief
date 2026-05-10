# ❖ NexusBrief — AI News Intelligence

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini AI](https://img.shields.io/badge/AI-Google_Gemini-7C6AF7?style=flat)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NexusBrief** is an executive-grade news intelligence platform that transforms the firehose of global information into digestible, professional insights. Using **Google Gemini Pro**, it monitors hundreds of live news sources, distills core takeaways, and renders them in a beautiful, high-performance interface.

---

## ⚡ Key Features

*   **Live AI Scraper**: Automated retrieval of real-time news across Finance, Tech, Science, and World topics via native RSS XML parsing.
*   **Executive Summaries**: High-density summaries and "3 Key Points" generated for every article using the `gemini-2.0-flash` model.
*   **Intelligent Sentiment Analysis**: Instant categorization of news impact (Positive, Negative, or Neutral).
*   **Unified Dashboard**: A sleek, dark-mode SPA (Single Page Application) with filtered search, category browsing, and reading time estimates.
*   **Automated Scheduler**: Daily background jobs using `APScheduler` to keep your news feed fresh without manual intervention.
*   **Full Auth System**: Secure user accounts with JWT authentication and cryptographically hashed passwords.

---

## 🛠 Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | **FastAPI** | High-performance, asynchronous Python web framework. |
| **AI Engine** | **Google Gemini** | Executive-tier summarization and insight extraction. |
| **Database** | **SQLAlchemy 2.0** | Modern Async ORM with SQLite (Dev) and PostgreSQL support. |
| **Auth** | **PyJWT + Passlib** | Secure Token-based authentication and Bcrypt hashing. |
| **Frontend** | **Vanilla JS/CSS** | Lightweight, lightning-fast SPA with zero binary dependencies. |
| **Dev Ops** | **Docker** | Fully containerized architecture for simple deployment. |

---

## 📂 Project Structure

```text
nexusbrief/
├── backend/
│   ├── main.py             # App entry point & lifespan management
│   ├── core/               # Configuration, Database, Security & Schemas
│   ├── models/             # SQLAlchemy ORM Models (User, Article, Category)
│   ├── routers/            # Modular API endpoints (Auth, News, Stats)
│   ├── services/           # Scheduler & Seed data logic
│   └── ai_engine/          # Gemini-powered scraper & summarizer
├── frontend/
│   └── index.html          # Professional SPA Interface
├── tests/                  # Pytest async test suite
├── cli.py                  # Management CLI tool (fetch, wipe, seed)
└── docker-compose.yml      # Container orchestration
```

---

## 🚀 Getting Started

### 1. Installation

```powershell
# Clone the repository
git clone https://github.com/your-vendor/nexusbrief
cd nexusbrief

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file from the template and add your Google Gemini API Key:

```env
DATABASE_URL=sqlite+aiosqlite:///nexusbrief.db
GEMINI_API_KEY=your_key_here
FETCH_LIVE=true
```

### 3. Initialize & Fetch

Use the custom **Nexus CLI** to populate your intelligence feed:

```powershell
# Fetch the latest news for all categories
python cli.py fetch --all
```

### 4. Launch

```powershell
# Start the FastAPI server
cd backend
uvicorn main:app --reload
```
Visit `http://localhost:8000` to see your news briefing.

---

## 🧪 Testing

NexusBrief comes with a comprehensive suite of asynchronous tests:

```powershell
python -m pytest tests/ -v
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
<p align="center">Made with ❤️ for the future of news intelligence.</p>

Open `.env` in VS Code and set your Gemini API key:
```
GEMINI_API_KEY=your_key_here
```

Get a free key at: https://aistudio.google.com/app/apikey

### 6. Start the server

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Or use the CLI from the project root:
```bash
python cli.py serve
```

### 7. Open the app

```
http://127.0.0.1:8000
```

The database is created automatically on first start. Demo articles are seeded
so the dashboard is populated immediately.

---

## API Documentation

Interactive Swagger UI is available at:
```
http://127.0.0.1:8000/api/docs
```

### Endpoints

```
GET  /api/v1/articles                # Paginated article list
GET  /api/v1/articles?category=tech  # Filter by category slug
GET  /api/v1/articles?sentiment=pos  # Filter by sentiment
GET  /api/v1/articles?search=AI      # Full-text search
GET  /api/v1/articles?sort=featured  # Sort order
GET  /api/v1/articles/featured       # Top 3 featured articles
GET  /api/v1/articles/{id}           # Single article
GET  /api/v1/categories              # All categories with article counts
GET  /api/v1/stats                   # Dashboard statistics
POST /api/v1/auth/signup             # Register new user
POST /api/v1/auth/login              # Authenticate user
GET  /api/v1/auth/me                 # Current user (requires JWT)
POST /api/v1/contact                 # Contact form submission
```

---

## CLI Reference

```bash
# Fetch AI-summarised news for all topics
python cli.py fetch --all

# Fetch a single topic
python cli.py fetch --topic "artificial intelligence" --category technology

# Use live RSS scraping (instead of mock corpus)
python cli.py fetch --all --live

# Re-seed the database with demo articles
python cli.py seed

# Delete articles older than 30 days
python cli.py prune

# Start the development server
python cli.py serve --reload

# Custom port
python cli.py serve --port 3000
```

---

## Running Tests

```bash
# Install test dependencies (included in requirements.txt)
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ -v --cov=backend --cov-report=term-missing
```

---

## Production Deployment

### Option 1 — Docker (recommended)

```bash
# Build and start
docker compose up --build

# With PostgreSQL
docker compose --profile postgres up --build

# Set environment variables in .env before starting
```

### Option 2 — Manual (Ubuntu / Debian)

```bash
# Install dependencies
pip install -r requirements.txt

# Switch to PostgreSQL in .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/nexusbrief

# Run database migrations
alembic upgrade head

# Start with Gunicorn + Uvicorn workers
pip install gunicorn
gunicorn backend.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

### Option 3 — Railway / Render / Fly.io (one-click)

These platforms auto-detect the Dockerfile and deploy automatically.
Set `GEMINI_API_KEY`, `DATABASE_URL`, and `SECRET_KEY` as environment variables
in the platform dashboard.

---

## Scheduled News Fetching

The scheduler runs automatically inside the FastAPI process:
- **Daily at 06:00 UTC** — fetches and summarises all 6 topic categories
- **Weekly on Sunday at 03:00 UTC** — prunes articles older than 30 days

To run a manual fetch at any time:
```bash
python cli.py fetch --all
```

To enable live RSS scraping (instead of mock corpus), set in `.env`:
```
FETCH_LIVE=true
```

---

## Switching to PostgreSQL

1. Install PostgreSQL locally or use a cloud provider (Supabase, Railway, etc.)
2. Create a database: `CREATE DATABASE nexusbrief;`
3. Update `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nexusbrief
   ```
4. Restart the server — tables are created automatically on startup.

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./nexusbrief.db` | Database connection string |
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `SECRET_KEY` | *(change in prod)* | JWT signing secret |
| `DEBUG` | `true` | Enable debug mode |
| `ARTICLES_PER_FETCH` | `5` | Articles fetched per topic per run |
| `MAX_ARTICLE_AGE_DAYS` | `30` | Articles older than this are pruned |
| `FETCH_LIVE` | `false` | Use live RSS vs mock corpus |

---

## License

MIT — © 2025 NexusBrief Inc.
