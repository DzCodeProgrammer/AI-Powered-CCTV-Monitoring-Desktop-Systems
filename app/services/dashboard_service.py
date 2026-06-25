from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

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
        .where(Attendance.detection_time >= start, Attendance.detection_time <= end)
    ) or 0

    attendance_recognized_today = db.scalar(
        select(func.count())
        .select_from(Attendance)
        .where(
            Attendance.detection_time >= start,
            Attendance.detection_time <= end,
            Attendance.status == STATUS_RECOGNIZED,
        )
    ) or 0

    attendance_unknown_today = db.scalar(
        select(func.count())
        .select_from(Attendance)
        .where(
            Attendance.detection_time >= start,
            Attendance.detection_time <= end,
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
