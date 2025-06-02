# Shelf
A service for uploading, processing, and managing book files.

## Features

- REST API for book management.
- Book metadata parsing (PDF, EPUB, MOBI) and management.
- Cover image extraction and storage.
- Metadata storage in a document-oriented database (MongoDB).
- File and cover storage in the local file system.
- Asynchronous processing for book uploads (Celery).

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
    Run MongoDB via Docker Compose:
    ```bash
    docker compose up
    ```

## Running the application

```bash
uvicorn main:app --reload
```

The API will be available at http://127.0.0.1:8000.
Interactive API documentation (Swagger UI) will be at http://127.0.0.1:8000/docs and an alternative documentation (ReDoc) is available at http://127.0.0.1:8000/redoc.

## TODO
- [ ] Implement MOBI/AZW3 parsing (potentially with Calibre CLI tools).
- [ ] More robust error handling and logging.
- [ ] User authentication and authorization.
- [ ] Full-text search capabilities.
- [ ] Implement task status polling if using true async processing for uploads.
- [ ] Refine cover extraction heuristics.
- [ ] Implement file renaming strategy after DB ID generation.
- [ ] Add comprehensive tests.