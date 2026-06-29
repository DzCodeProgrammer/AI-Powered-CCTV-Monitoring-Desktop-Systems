"""Local timezone formatting (default: Asia/Jakarta / WIB)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.utils.config import get_settings

DEFAULT_TIMEZONE = "Asia/Jakarta"
DEFAULT_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def get_app_timezone() -> ZoneInfo:
    settings = get_settings()
    tz_name = (settings.timezone or DEFAULT_TIMEZONE).strip()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def utc_to_local(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(get_app_timezone())


def format_datetime_local(
    value: datetime | None,
    *,
    fmt: str = DEFAULT_DATETIME_FMT,
    include_zone: bool = True,
) -> str:
    if value is None:
        return "-"
    local_dt = utc_to_local(value)
    if include_zone:
        zone = local_dt.tzname() or get_app_timezone().key
        return f"{local_dt.strftime(fmt)} {zone}"
    return local_dt.strftime(fmt)


def now_local() -> datetime:
    return datetime.now(get_app_timezone())
