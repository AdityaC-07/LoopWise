import asyncio
import datetime
import logging
from celery import Celery
from app.core.config import get_settings
from app.models.database import AsyncSessionLocal
from app.analytics.aggregator import compute_ward_rollup

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "loopwise_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        "nightly-ward-rollup": {
            "task": "app.analytics.tasks.nightly_rollup",
            "schedule": 86400.0,  # Once daily
        }
    }
)


@celery_app.task
def aggregate_ward_day(ward_id: str, date_str: str):
    """Celery task to compute ward rollup for a specific day."""
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    
    async def _run():
        async with AsyncSessionLocal() as session:
            await compute_ward_rollup(session, ward_id, date)

    asyncio.run(_run())
    logger.info(f"Completed Celery rollup for ward {ward_id} on {date_str}.")


@celery_app.task
def nightly_rollup():
    """Nightly Celery beat task recomputing rollups for active wards."""
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    for ward_id in ["WD-001", "WD-002", "WD-003"]:
        aggregate_ward_day.delay(ward_id, yesterday)
