"""Wait for database and create tables on startup."""

from __future__ import annotations

import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database.base import Base
from app.database.connection import engine
from app.database.migrate import run_migrations
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_RETRIES = 30
RETRY_DELAY_SECONDS = 2


def wait_for_db() -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established (%s)", settings.db_driver)
            return
        except OperationalError as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Database unavailable after {MAX_RETRIES} attempts. "
                    f"Driver={settings.db_driver}. "
                    "Start MySQL: docker compose up -d"
                ) from exc
            logger.warning(
                "Database not ready (attempt %s/%s): %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            time.sleep(RETRY_DELAY_SECONDS)


def init_db() -> None:
    import app.models  # noqa: F401

    wait_for_db()
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
