from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.face_recognition.recognizer import STATUS_RECOGNIZED, STATUS_UNKNOWN
from app.models.attendance import Attendance
from app.models.detection import Detection
from app.models.unknown_face import UnknownFace
from app.models.user import User


@dataclass
class AttendanceStats:
    total_today: int
    recognized_today: int
    unknown_today: int
    total_all_time: int


@dataclass
class DashboardStats:
    registered_users: int
    detections_today: int
    unknown_detections_today: int
    unknown_faces_total: int
    attendance: AttendanceStats


def _today_bounds() -> tuple[datetime, datetime]:
    today = date.today()
    return (
        datetime.combine(today, time.min),
        datetime.combine(today, time.max),
    )


def get_dashboard_stats(db: Session) -> DashboardStats:
    start, end = _today_bounds()

    registered_users = db.scalar(select(func.count()).select_from(User)) or 0

    detections_today = db.scalar(
        select(func.count())
        .select_from(Detection)
        .where(Detection.timestamp >= start, Detection.timestamp <= end)
    ) or 0

    unknown_detections_today = db.scalar(
        select(func.count())
        .select_from(Detection)
        .where(
            Detection.timestamp >= start,
            Detection.timestamp <= end,
            Detection.status == STATUS_UNKNOWN,
        )
    ) or 0

    unknown_faces_total = db.scalar(select(func.count()).select_from(UnknownFace)) or 0

    attendance_total_today = db.scalar(
        select(func.count())
        .select_from(Attendance)
        .where(Attendance.detected_at >= start, Attendance.detected_at <= end)
    ) or 0

    attendance_recognized_today = db.scalar(
        select(func.count())
        .select_from(Attendance)
        .where(
            Attendance.detected_at >= start,
            Attendance.detected_at <= end,
            Attendance.status == STATUS_RECOGNIZED,
        )
    ) or 0

    attendance_unknown_today = db.scalar(
        select(func.count())
        .select_from(Attendance)
        .where(
            Attendance.detected_at >= start,
            Attendance.detected_at <= end,
            Attendance.status == STATUS_UNKNOWN,
        )
    ) or 0

    attendance_all_time = db.scalar(select(func.count()).select_from(Attendance)) or 0

    return DashboardStats(
        registered_users=registered_users,
        detections_today=detections_today,
        unknown_detections_today=unknown_detections_today,
        unknown_faces_total=unknown_faces_total,
        attendance=AttendanceStats(
            total_today=attendance_total_today,
            recognized_today=attendance_recognized_today,
            unknown_today=attendance_unknown_today,
            total_all_time=attendance_all_time,
        ),
    )


def get_recent_activity(db: Session, limit: int = 20) -> list[Detection]:
    return list(
        db.scalars(
            select(Detection).order_by(Detection.timestamp.desc()).limit(limit)
        ).all()
    )


@dataclass
class UserAttendanceStat:
    user_id: int
    full_name: str
    image_filename: str
    total_checkins: int
    period_checkins: int
    active_days: int
    period_days: int
    avg_per_active_day: float
    avg_per_calendar_day: float
    last_attendance: datetime | None
    avg_confidence: float | None


def get_user_attendance_statistics(
    db: Session,
    period_days: int = 30,
) -> list[UserAttendanceStat]:
    period_days = max(1, min(period_days, 365))
    period_start = datetime.combine(
        date.today() - timedelta(days=period_days - 1),
        time.min,
    )

    users = list(
        db.scalars(
            select(User).where(User.is_active.is_(True)).order_by(User.full_name)
        ).all()
    )

    stats: list[UserAttendanceStat] = []
    for user in users:
        total_checkins = db.scalar(
            select(func.count())
            .select_from(Attendance)
            .where(Attendance.user_id == user.id)
        ) or 0

        period_rows = list(
            db.scalars(
                select(Attendance)
                .where(
                    Attendance.user_id == user.id,
                    Attendance.detected_at >= period_start,
                )
                .order_by(Attendance.detected_at.desc())
            ).all()
        )
        period_checkins = len(period_rows)

        active_days = len(
            {
                row.detected_at.date()
                for row in period_rows
                if row.detected_at is not None
            }
        )

        confidences = [
            row.confidence
            for row in period_rows
            if row.confidence is not None
        ]
        avg_confidence = (
            float(sum(confidences) / len(confidences)) if confidences else None
        )

        last_attendance = period_rows[0].detected_at if period_rows else None
        if last_attendance is None and total_checkins:
            last_row = db.scalar(
                select(Attendance)
                .where(Attendance.user_id == user.id)
                .order_by(Attendance.detected_at.desc())
                .limit(1)
            )
            if last_row:
                last_attendance = last_row.detected_at

        image_filename = Path(user.image_path).name.replace("\\", "/").split("/")[-1]

        stats.append(
            UserAttendanceStat(
                user_id=user.id,
                full_name=user.full_name,
                image_filename=image_filename,
                total_checkins=total_checkins,
                period_checkins=period_checkins,
                active_days=active_days,
                period_days=period_days,
                avg_per_active_day=(
                    round(period_checkins / active_days, 2) if active_days else 0.0
                ),
                avg_per_calendar_day=round(period_checkins / period_days, 2),
                last_attendance=last_attendance,
                avg_confidence=(
                    round(avg_confidence, 3) if avg_confidence is not None else None
                ),
            )
        )

    stats.sort(key=lambda item: item.period_checkins, reverse=True)
    return stats
