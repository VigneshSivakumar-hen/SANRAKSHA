"""
Optional background scheduler: periodically calls sync_all_locations() so
the dashboard stays fresh without a human hitting /api/sync/run manually.

Off by default (ENABLE_SCHEDULER=false) so tests and quick local runs stay
predictable; a monitoring dashboard for a live deployment would want this on.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

_scheduler = None


def _sync_job():
    from app.services import prediction_service

    db = SessionLocal()
    try:
        results = prediction_service.sync_all_locations(db)
        logger.info("Scheduled sync complete: %s", results)
    finally:
        db.close()


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_sync_job, "interval", minutes=settings.SYNC_INTERVAL_MINUTES)
    _scheduler.start()
    logger.info("Sync scheduler started (every %s minutes)", settings.SYNC_INTERVAL_MINUTES)
