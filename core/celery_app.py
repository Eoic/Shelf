from celery import Celery

from .config import settings

if settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND:
    celery_app = Celery(
        "book_manager_tasks",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["services.book_tasks"],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        worker_concurrency=4,
        task_routes={"tasks.add": "low-priority"},
    )
else:
    celery_app = None

# NOTE:
# Run Celery worker with:
# celery -A core.celery_app worker -l info
