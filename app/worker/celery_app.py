from celery import Celery
from app.core.config import settings

celery_app = Celery("worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.task_routes = {"app.worker.test_celery": "main-queue"}

@celery_app.task(name="test_celery")
def test_celery(word: str) -> str:
    return f"test task return {word}"
