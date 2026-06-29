"""Attendance shift windows — masuk (07:00–16:59) and pulang (17:00–06:59) WIB."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.utils.datetime_local import utc_to_local

ShiftKind = Literal["masuk", "pulang"]

MASUK_START_HOUR = 7
MASUK_END_HOUR = 16
MASUK_END_MINUTE = 59
PULANG_START_HOUR = 17
PULANG_END_HOUR = 6
PULANG_END_MINUTE = 59


def current_shift(at: datetime | None = None) -> ShiftKind:
    """Return masuk (07:00–16:59) or pulang (17:00–06:59) in local timezone."""
    local = utc_to_local(at or datetime.utcnow())
    minutes = local.hour * 60 + local.minute
    masuk_start = MASUK_START_HOUR * 60
    masuk_end = MASUK_END_HOUR * 60 + MASUK_END_MINUTE
    if masuk_start <= minutes <= masuk_end:
        return "masuk"
    return "pulang"


def shift_label(shift: ShiftKind) -> str:
    return "Masuk" if shift == "masuk" else "Pulang"


def shift_window_utc(shift: ShiftKind, at: datetime | None = None) -> tuple[datetime, datetime]:
    """UTC-naive bounds matching attendance_logs.detected_at storage."""
    local = utc_to_local(at or datetime.utcnow())

    if shift == "masuk":
        start_local = local.replace(
            hour=MASUK_START_HOUR, minute=0, second=0, microsecond=0
        )
        end_local = local.replace(
            hour=MASUK_END_HOUR, minute=MASUK_END_MINUTE, second=59, microsecond=999999
        )
    elif local.hour >= PULANG_START_HOUR:
        start_local = local.replace(
            hour=PULANG_START_HOUR, minute=0, second=0, microsecond=0
        )
        end_local = (local + timedelta(days=1)).replace(
            hour=PULANG_END_HOUR, minute=PULANG_END_MINUTE, second=59, microsecond=999999
        )
    else:
        start_local = (local - timedelta(days=1)).replace(
            hour=PULANG_START_HOUR, minute=0, second=0, microsecond=0
        )
        end_local = local.replace(
            hour=PULANG_END_HOUR, minute=PULANG_END_MINUTE, second=59, microsecond=999999
        )

    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def count_attendance_in_shift(
    db: Session,
    user_id: int,
    shift: ShiftKind,
    at: datetime | None = None,
) -> int:
    start, end = shift_window_utc(shift, at)
    return (
        db.scalar(
            select(func.count())
            .select_from(Attendance)
            .where(
                Attendance.user_id == user_id,
                Attendance.detected_at >= start,
                Attendance.detected_at <= end,
            )
        )
        or 0
    )


def should_notify_attendance_wa(
    db: Session,
    user_id: int,
    at: datetime | None = None,
) -> tuple[bool, ShiftKind]:
    """One WhatsApp per user per shift window (max 2/day: masuk + pulang)."""
    shift = current_shift(at)
    count = count_attendance_in_shift(db, user_id, shift, at)
    return count == 1, shift
