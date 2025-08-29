# Project Agents.md guide for OpenAI Codex

This Agents.md file provides comprehensive guidance for OpenAI Codex and other AI agents working with this codebase.

## Project structure for OpenAI Codex navigation

- `/api`: FastAPI route handlers and request/response schemas
- `/core`: Application core (auth helpers, configuration, celery setup, logging)
- `/database`: Database layer, async SQLAlchemy engine setup, and CRUD utilities
- `/models`: SQLAlchemy ORM models and domain models
- `/parsers`: File parsers for supported book formats (e.g., PDF, EPUB)
- `/services`: Business logic and storage backends (e.g., filesystem, MinIO)
- `/config`: Project configuration files (e.g., Redis settings)
- `/alembic`: Migration environment and versioned migration scripts
- `/storage`: Runtime file storage for uploaded/processed books (do not edit directly)
- `main.py`: FastAPI application entrypoint
- `pyproject.toml`: Tooling and dependency configuration
- `/tests`: Test modules (`test_*.py` / `tests_*.py`) for validating project functionality

## Coding conventions for OpenAI Codex

### General conventions for Agents.md implementation

- Use **Python 3.11+** for all code
- Follow **PEP 8** style, formatted with **Black** (line length 120) and **isort**
- Lint with **ruff**; fix reported issues before committing
- Write expressive function and variable names and include docstrings
- Add comments explaining non-trivial or performance-critical logic

### FastAPI and service module guidelines for OpenAI Codex

- Prefer `async`/`await` in endpoints and service functions
- Keep route handlers thin; delegate heavy logic to service modules
- Define request/response models with **Pydantic**
- Use snake_case filenames for modules (e.g., `book_service.py`)

### Database and migration guidelines for OpenAI Codex

- Define models using SQLAlchemy's declarative syntax
- Generate an Alembic migration for each schema change
- Keep migrations idempotent and clearly documented

### Parser and storage guidelines for OpenAI Codex

- Implement new parsers by extending `parsers.base_parser.BaseParser`
- Keep parser classes small and format-agnostic
- For storage backends, implement the `services.storage.storage_backend.StorageBackend` interface

## Testing requirements for OpenAI Codex

Run tests with the following commands:

```
# Run all tests
pytest

# Run a specific test file
pytest path/to/test_file.py

# Run tests with coverage
pytest --cov
```

## Pull request guidelines for OpenAI Codex

1. Provide a clear description of the change
2. Reference related issues or tickets
3. Ensure all tests pass and code is formatted and linted
4. Include API docs or example requests and responses for new endpoints
5. Keep each pull request focused on a single feature or fix

## Programmatic checks for OpenAI Codex

Before submitting changes, run:

```
# Lint check
ruff .

# Format check
black --check .
# Type check
mypy .

# Run tests
pytest
```

All checks must pass before OpenAI Codex-generated code can be merged.
