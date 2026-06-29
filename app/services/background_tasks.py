"""Async maintenance loop: monitoring schedule and disk cleanup."""

from __future__ import annotations

import asyncio

from app.services.cleanup_service import maybe_run_cleanup, run_cleanup
from app.services.schedule_service import apply_monitor_schedule
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("background")

TICK_SECONDS = 60


async def maintenance_loop() -> None:
    settings = get_settings()
    if settings.cleanup_enabled:
        try:
            run_cleanup(settings)
        except Exception as exc:
            logger.warning("Startup cleanup failed: %s", exc)

    while True:
        try:
            get_settings.cache_clear()
            settings = get_settings()
            apply_monitor_schedule(settings)
            maybe_run_cleanup(settings)
        except Exception as exc:
            logger.warning("Maintenance tick failed: %s", exc)
        await asyncio.sleep(TICK_SECONDS)
