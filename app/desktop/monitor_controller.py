"""Start/stop live monitoring for the desktop app."""

from __future__ import annotations

from app.camera.stream_broadcaster import LiveStreamBroadcaster
from app.database.connection import SessionLocal
from app.face_recognition.recognizer import STATUS_DETECTING, RecognitionEvent
from app.services.attendance_service import log_attendance
from app.services.detection_service import log_matches
from app.services.monitoring_service import is_monitoring_active, start_monitoring, stop_monitoring
from app.services.recognition_service import get_recognizer
from app.utils.config import Settings, get_settings


def resolve_camera_source(settings: Settings, override: str | None = None) -> str:
    source = (override if override is not None else settings.camera_source).strip()
    lowered = source.lower()
    if lowered in {"dahua", "ip", "cctv"}:
        if settings.rtsp_url:
            return settings.rtsp_url
        return settings.dahua_rtsp_url
    if lowered.startswith("rtsp://"):
        return source
    return source


def start_desktop_monitoring(source_override: str | None = None) -> None:
    settings = get_settings()
    source = resolve_camera_source(settings, source_override)
    recognizer = get_recognizer()
    start_monitoring()

    def on_recognition(event: RecognitionEvent) -> None:
        if event.match.status == STATUS_DETECTING:
            return
        session = SessionLocal()
        try:
            current = get_settings()
            log_matches(
                session,
                current,
                event.annotated_frame,
                [event.match],
                source,
            )
            log_attendance(session, current, [event.match], source)
        finally:
            session.close()

    LiveStreamBroadcaster.get().ensure_running(
        settings,
        recognizer,
        source,
        on_recognition=on_recognition,
    )


def stop_desktop_monitoring() -> None:
    stop_monitoring()


def monitoring_active() -> bool:
    return is_monitoring_active()


def camera_last_error() -> str | None:
    return LiveStreamBroadcaster.get().last_error
