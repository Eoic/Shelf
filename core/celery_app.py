from celery import Celery
from .config import settings

# Only initialize Celery if URLs are configured
if settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND:
    celery_app = Celery(
        "book_manager_tasks",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            # Add paths to your task modules here, e.g.:
            # "services.book_tasks"
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        # task_routes = {'tasks.add': 'low-priority'}, # Example routing
        # worker_concurrency = 4, # Example concurrency
    )
else:
    celery_app = None  # type: ignore

# To run a Celery worker (if using Celery):
# celery -A core.celery_app worker -l info
