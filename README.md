# Shelf
A service for uploading, processing, and managing book files.

## Features

- REST API for book management.
- Book metadata parsing (e.g. PDF, EPUB, MOBI) and management..
- Book file and cover storage that supports various storage methods (e.g. MinIO, Google Drive).
- Asynchronous processing for book uploads.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Shelf
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Setup environment variables:**
    Copy `.env.example` to `.env` and update the values as needed.

5.  **Ensure your database is running.**
    Run PostgreSQL via Docker Compose:
    ```bash
    docker compose up
    ```

## Running the application

```bash
uvicorn main:app --reload
```

The API will be available at http://127.0.0.1:8000.
Interactive API documentation (Swagger UI) will be at http://127.0.0.1:8000/docs and an alternative documentation (ReDoc) is available at http://127.0.0.1:8000/redoc.

## Running Celery worker

To process background tasks (such as book uploads and metadata extraction), you need to run a Celery worker. Make sure your Redis and PostgreSQL services are running and your environment variables are set (see `.env.example`).

### Start Celery worker (locally):

```bash
celery -A core.celery.celery_app worker --loglevel=info
```

- If you want to specify a queue:

```bash
celery -A core.celery.celery_app worker --loglevel=info -Q default
```

## Database and migrations

This project uses **PostgreSQL** as the main database via SQLAlchemy (async) and Alembic for migrations.

- Ensure PostgreSQL is running (see Docker Compose instructions above).
- Database connection settings are configured via environment variables in `.env` (see `.env.example`).
- To create or update the database schema, use Alembic migrations:

### Creating a new migration after model changes

```bash
alembic revision --autogenerate -m "Describe your change"
```

### Applying migrations to the database

```bash
alembic upgrade head
```

- Alembic configuration is in `alembic.ini` and migration scripts are in the `alembic/versions/` directory.

## TODO
- Support more file formats (e.g. CBZ, CBR).
- Allow full-text search (PostgreSQL or Elasticsearch).
- Allow creating text highlights and notes.
- Update metadata from external sources (e.g. Google Books, Open Library).
- Reading progress tracking and bookmarks.
- Recommendations based on reading history.
- Search by metadata and fuzzy search. 
- Webhooks and event system for real-time updates.
- Statistics tracking (e.g. reading time, books/pages read).
- Bulk uploading and processing.
- Conversion between formats (e.g. PDF to EPUB).
- Bulk file and metadata export.
- Audit logs.