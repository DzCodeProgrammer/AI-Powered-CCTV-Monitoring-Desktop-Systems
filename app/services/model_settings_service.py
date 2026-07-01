"""Persist recognition tuning values to .env and reload runtime settings."""

from __future__ import annotations

import re
from pathlib import Path

from app.face_recognition.detector import FaceDetector
from app.services.recognition_service import get_recognizer
from app.services.schedule_service import apply_monitor_schedule, normalize_hhmm, parse_hhmm
from app.utils.config import Settings, get_settings

_ENV_PATH = Path(".env")

LAPTOP_8GB_PRESET: dict[str, str] = {
    "LOW_END_MODE": "true",
    "FACE_MODEL": "Facenet512",
    "RECOGNITION_THRESHOLD": "0.45",
    "RECOGNITION_MARGIN": "0.08",
    "RECOGNITION_INTERVAL": "1",
    "DETECTION_INTERVAL": "1",
    "FRAME_SKIP": "1",
    "DETECTION_FRAME_SKIP": "1",
    "PROCESS_MAX_WIDTH": "640",
    "STREAM_MAX_WIDTH": "640",
    "JPEG_QUALITY": "70",
    "MAX_FACES_PER_FRAME": "2",
    "ATTENDANCE_INTERVAL": "60",
}


def update_env_file(updates: dict[str, str], env_path: Path | None = None) -> None:
    path = env_path or _ENV_PATH
    if not path.is_file():
        raise FileNotFoundError(f".env not found at {path.resolve()}")

    content = path.read_text(encoding="utf-8")
    for key, value in updates.items():
        pattern = rf"^(\s*{re.escape(key)}\s*=\s*).*$"
        if re.search(pattern, content, flags=re.MULTILINE | re.IGNORECASE):
            content = re.sub(
                pattern,
                rf"\g<1>{value}",
                content,
                count=1,
                flags=re.MULTILINE | re.IGNORECASE,
            )
        else:
            if content and not content.endswith("\n"):
                content += "\n"
            content += f"{key}={value}\n"

    path.write_text(content, encoding="utf-8")


def apply_recognition_settings_to_runtime(settings: Settings) -> None:
    try:
        recognizer = get_recognizer()
    except RuntimeError:
        return

    recognizer.settings = settings
    recognizer.detector = FaceDetector(settings)
    recognizer.refresh_performance(settings)


def _format_interval(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def save_model_settings(
    *,
    recognition_threshold: float,
    recognition_margin: float,
    recognition_interval: float,
    frame_skip: int,
    process_max_width: int,
    max_faces_per_frame: int,
) -> Settings:
    if not 0.2 <= recognition_threshold <= 0.8:
        raise ValueError("Recognition threshold must be between 0.2 and 0.8.")
    if not 0.01 <= recognition_margin <= 0.25:
        raise ValueError("Recognition margin must be between 0.01 and 0.25.")
    if not 1.0 <= recognition_interval <= 300.0:
        raise ValueError("Recognition interval must be between 1 and 300 seconds.")
    if not 1 <= frame_skip <= 6:
        raise ValueError("Frame skip must be between 1 and 6.")
    if not 320 <= process_max_width <= 1280:
        raise ValueError("Process max width must be between 320 and 1280.")
    if not 1 <= max_faces_per_frame <= 4:
        raise ValueError("Max faces per frame must be between 1 and 4.")

    update_env_file(
        {
            "RECOGNITION_THRESHOLD": f"{recognition_threshold:.2f}",
            "RECOGNITION_MARGIN": f"{recognition_margin:.2f}",
            "RECOGNITION_INTERVAL": _format_interval(recognition_interval),
            "DETECTION_INTERVAL": _format_interval(recognition_interval),
            "FRAME_SKIP": str(frame_skip),
            "PROCESS_MAX_WIDTH": str(process_max_width),
            "MAX_FACES_PER_FRAME": str(max_faces_per_frame),
        }
    )

    get_settings.cache_clear()
    settings = get_settings()
    apply_recognition_settings_to_runtime(settings)
    return settings


def apply_laptop_8gb_preset() -> Settings:
    update_env_file(LAPTOP_8GB_PRESET.copy())
    get_settings.cache_clear()
    settings = get_settings()
    apply_recognition_settings_to_runtime(settings)
    return settings


def save_recognition_settings(
    *,
    recognition_threshold: float,
    recognition_margin: float,
    recognition_interval: float,
) -> Settings:
    """Backward-compatible wrapper using current performance values."""
    current = get_settings()
    return save_model_settings(
        recognition_threshold=recognition_threshold,
        recognition_margin=recognition_margin,
        recognition_interval=recognition_interval,
        frame_skip=current.frame_skip,
        process_max_width=current.process_max_width,
        max_faces_per_frame=current.max_faces_per_frame,
    )


def form_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "on", "yes"}


def save_operations_settings(
    *,
    monitor_schedule_enabled: bool,
    monitor_schedule_start: str,
    monitor_schedule_end: str,
    cleanup_enabled: bool,
    log_retention_days: int,
    screenshot_retention_days: int,
    cleanup_interval_hours: int,
) -> Settings:
    start = normalize_hhmm(monitor_schedule_start)
    end = normalize_hhmm(monitor_schedule_end)
    parse_hhmm(start)
    parse_hhmm(end)

    if not 1 <= log_retention_days <= 365:
        raise ValueError("Log retention must be between 1 and 365 days.")
    if not 1 <= screenshot_retention_days <= 365:
        raise ValueError("Screenshot retention must be between 1 and 365 days.")
    if not 1 <= cleanup_interval_hours <= 168:
        raise ValueError("Cleanup interval must be between 1 and 168 hours.")

    update_env_file(
        {
            "MONITOR_SCHEDULE_ENABLED": "true" if monitor_schedule_enabled else "false",
            "MONITOR_SCHEDULE_START": start,
            "MONITOR_SCHEDULE_END": end,
            "CLEANUP_ENABLED": "true" if cleanup_enabled else "false",
            "LOG_RETENTION_DAYS": str(log_retention_days),
            "SCREENSHOT_RETENTION_DAYS": str(screenshot_retention_days),
            "CLEANUP_INTERVAL_HOURS": str(cleanup_interval_hours),
        }
    )

    get_settings.cache_clear()
    settings = get_settings()
    apply_monitor_schedule(settings)
    return settings


def save_notification_settings(
    *,
    wa_notify_enabled: bool,
    wa_api_token: str,
    wa_admin_phones: str,
    wa_notify_unknown: bool,
    wa_notify_attendance: bool,
) -> Settings:
    token = wa_api_token.strip()
    if wa_notify_enabled and not token:
        raise ValueError("WA API token is required when WhatsApp notifications are enabled.")

    update_env_file(
        {
            "WA_NOTIFY_ENABLED": "true" if wa_notify_enabled else "false",
            "WA_API_TOKEN": token,
            "WA_ADMIN_PHONES": wa_admin_phones.strip(),
            "WA_NOTIFY_UNKNOWN": "true" if wa_notify_unknown else "false",
            "WA_NOTIFY_ATTENDANCE": "true" if wa_notify_attendance else "false",
        }
    )

    get_settings.cache_clear()
    return get_settings()


def save_camera_settings(*, dahua_subtype: int) -> Settings:
    if dahua_subtype not in (0, 1):
        raise ValueError("DAHUA_SUBTYPE must be 0 (main stream) or 1 (substream).")

    update_env_file({"DAHUA_SUBTYPE": str(dahua_subtype)})

    from app.camera.manager import CameraManager

    CameraManager.reset()
    get_settings.cache_clear()
    return get_settings()
