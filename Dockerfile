# ─── NexusBrief Dockerfile ────────────────────────────────────────────────────
# Multi-stage build: lean production image ~180MB
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─── Dependencies ────────────────────────────────────────────────────────────
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─── Production image ─────────────────────────────────────────────────────────
FROM deps AS production

# Copy application code
COPY backend/   /app/backend/
COPY frontend/  /app/frontend/
COPY cli.py     /app/cli.py
COPY .env.example /app/.env.example

# Set PYTHONPATH so `import core`, `import models` etc. resolve from /app/backend
ENV PYTHONPATH=/app/backend
ENV PORT=8000

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/docs || exit 1

# Start server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--log-level", "info"]
