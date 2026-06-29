"""Automatic monitoring start/stop by time-of-day window."""

from __future__ import annotations

import re
from datetime import datetime, time

from app.services.monitoring_service import is_monitoring_active, start_monitoring, stop_monitoring
from app.utils.config import Settings
from app.utils.logging import get_logger

logger = get_logger("schedule")

_TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})$")


def normalize_hhmm(value: str) -> str:
    """Accept HH:MM or HH:MM:SS (HTML time inputs)."""
    match = re.match(r"^(\d{1,2}):(\d{2})", value.strip())
    if not match:
        raise ValueError("Time must be HH:MM (e.g. 07:00).")
    hour = int(match.group(1))
    minute = int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Time must be a valid 24-hour clock value.")
    return f"{hour:02d}:{minute:02d}"


def parse_hhmm(value: str) -> time:
    normalized = normalize_hhmm(value)
    match = _TIME_PATTERN.match(normalized)
    if not match:
        raise ValueError("Time must be HH:MM (e.g. 07:00).")
    hour = int(match.group(1))
    minute = int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Time must be a valid 24-hour clock value.")
    return time(hour=hour, minute=minute)


def is_within_schedule(start: str, end: str, *, now: time | None = None) -> bool:
    start_time = parse_hhmm(start)
    end_time = parse_hhmm(end)
    current = now or datetime.now().time()

    if start_time <= end_time:
        return start_time <= current <= end_time
    return current >= start_time or current <= end_time


def schedule_status(settings: Settings) -> dict[str, str | bool]:
    if not settings.monitor_schedule_enabled:
        return {
            "enabled": False,
            "within_window": False,
            "label": "Schedule disabled",
        }

    within = is_within_schedule(
        settings.monitor_schedule_start,
        settings.monitor_schedule_end,
    )
    label = (
        f"Active window {settings.monitor_schedule_start}–{settings.monitor_schedule_end}"
        if within
        else f"Outside window {settings.monitor_schedule_start}–{settings.monitor_schedule_end}"
    )
    return {
        "enabled": True,
        "within_window": within,
        "label": label,
    }


def apply_monitor_schedule(settings: Settings) -> str | None:
    """Start or stop monitoring to match schedule. Returns action taken or None."""
    if not settings.monitor_schedule_enabled:
        return None

    within = is_within_schedule(
        settings.monitor_schedule_start,
        settings.monitor_schedule_end,
    )
    active = is_monitoring_active()

    if within and not active:
        start_monitoring()
        logger.info(
            "Schedule started monitoring (%s–%s)",
            settings.monitor_schedule_start,
            settings.monitor_schedule_end,
        )
        return "started"

    if not within and active:
        stop_monitoring()
        logger.info(
            "Schedule stopped monitoring (outside %s–%s)",
            settings.monitor_schedule_start,
            settings.monitor_schedule_end,
        )
        return "stopped"

    return None
