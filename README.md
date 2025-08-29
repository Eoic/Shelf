# Shelf

Shelf is a FastAPI-powered service for uploading, processing, and managing book files. It is designed to serve as the backend for mobile or web applications that need digital library capabilities.

## Features

- RESTful API for creating, retrieving, updating, and deleting books and shelves.
- Automatic metadata parsing for common ebook formats (PDF, EPUB, MOBI).
- Pluggable storage backends (local filesystem, MinIO, etc.).
- Asynchronous processing of uploads using Celery.
- Configurable CORS support for frontend integration.

## Architecture overview

```
api/        FastAPI route handlers and Pydantic schemas
core/       application core (auth, configuration, celery, logging)
database/   async SQLAlchemy engine and CRUD utilities
models/     SQLAlchemy ORM models and domain classes
parsers/    format-specific book parsers
services/   business logic and storage backends
```

## Quick start

### Requirements

- Python 3.11+
- Docker (for PostgreSQL, Redis, MinIO)

### Installation

```bash
git clone <repository-url>
cd Shelf
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # or pip install -e .[dev]
cp .env.example .env
docker compose up -d
```

### Run the API

```bash
uvicorn main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

### Run background worker

```bash
celery -A core.celery.celery_app worker --loglevel=info
```

## Using Shelf as a backend

After configuring `CORS_ORIGINS` in `.env`, any web or mobile client can interact with the service:

```bash
# Upload a book
curl -X POST "http://127.0.0.1:8000/api/v1/books" -F file=@book.epub

# List books
curl "http://127.0.0.1:8000/api/v1/books"
```

## Configuration

Key environment variables:

- `POSTGRES_*` – PostgreSQL connection settings.
- `MINIO_*` – object storage configuration.
- `CELERY_*` – Celery broker and backend URLs.
- `CORS_ORIGINS` – comma-separated list of allowed origins for CORS (e.g. `"http://localhost:3000,https://example.com"`; use `"*"` to allow all).

## Development and testing

```bash
ruff .
black --check .
mypy .
pytest
```

## Roadmap

- Support more file formats (e.g. CBZ, CBR)
- Allow full-text search (PostgreSQL or Elasticsearch)
- Allow creating text highlights and notes
- Update metadata from external sources (e.g. Google Books, Open Library)
- Reading progress tracking and bookmarks
- Recommendations based on reading history
- Search by metadata and fuzzy search
- Webhooks and event system for real-time updates
- Statistics tracking (e.g. reading time, books/pages read)
- Bulk uploading and processing
- Conversion between formats (e.g. PDF to EPUB)
- Bulk file and metadata export
- Audit logs
