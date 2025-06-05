from celery import Celery

from .config import settings

if settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND:
    celery_app = Celery(
        "shelf_tasks",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        worker_concurrency=4,
        task_routes={"tasks.add": {"queue": "default"}},
        task_default_queue="default",
        task_default_exchange="default",
        task_default_routing_key="default",
    )
else:
    celery_app = None
