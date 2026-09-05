# syntax=docker/dockerfile:1
FROM python:3.12-slim

# System libraries needed at *runtime* by weasyprint (used by the report-generation CLI,
# main.py, for markdown_to_pdf) — pip alone can't install these, and it's the main reason
# this backend is awkward to set up outside a container. The api.py service itself doesn't
# need them, but both share this one Poetry project. (pdfkit is also declared in
# pyproject.toml but isn't imported anywhere in the code, so its wkhtmltopdf system
# dependency — no longer packaged in Debian anyway — is intentionally left out.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-ansi

COPY . .

EXPOSE 8000

# Production-safe default (no --reload) -- this is the command a real host (Railway,
# Fly.io, a VM, etc.) would run from this same image. docker-compose.yml overrides this
# with --reload for local live-editing; that override is dev-only, not baked into the image.
# The heavier report-generation CLI is available in the same image via:
#   docker compose exec backend python main.py
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
