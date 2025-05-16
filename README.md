# Shelf
An e-book storage server.

A FastAPI application for uploading, processing, and managing e-book files.

## Features (Planned/Implemented)

- REST API for e-book management.
- E-book parsing for metadata (EPUB, PDF planned).
- Cover image extraction and storage.
- Metadata storage in a document-oriented database (MongoDB example).
- File and cover storage in the local file system.
- Asynchronous processing for e-book uploads (via FastAPI BackgroundTasks, Celery optional).

## Project Structure

(Briefly describe the main directories)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd ebook_manager
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy `.env.example` to `.env` and update the values, especially for the database connection and storage paths.
    ```bash
    cp .env.example .env
    # Nano .env or code .env to edit
    ```

5.  **Ensure your database is running.**
    If using MongoDB as per example, make sure it's accessible at the URL specified in `.env`.

## Running the Application

```bash
uvicorn main:app --reload
# gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

The API will be available at http://127.0.0.1:8000.
Interactive API documentation (Swagger UI) will be at http://127.0.0.1:8000/docs.
Alternative documentation (ReDoc) at http://127.0.0.1:8000/redoc.

Running Celery Worker (Optional)

If you implement and use Celery for background tasks:
```
celery -A core.celery_app worker -l info
```

Running Tests (TODO)
```
pytest
```
Implement MOBI/AZW3 parsing (potentially with Calibre CLI tools).
More robust error handling and logging.
User authentication and authorization.
Full-text search capabilities.
Implement task status polling if using true async processing for uploads.
Refine cover extraction heuristics.
Implement file renaming strategy after DB ID generation.
Add comprehensive tests.