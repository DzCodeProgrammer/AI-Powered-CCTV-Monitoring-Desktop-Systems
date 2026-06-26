"""Global live monitoring state — start/stop camera and recognition pipeline."""

from __future__ import annotations

import threading
import time

import cv2

from app.camera.frames import make_status_frame
from app.camera.manager import CameraManager
from app.services.recognition_service import get_recognizer
from app.utils.config import Settings
from app.utils.logging import get_logger

logger = get_logger("monitoring")

_lock = threading.Lock()
_monitoring_active = False


def is_monitoring_active() -> bool:
    with _lock:
        return _monitoring_active


def start_monitoring() -> None:
    with _lock:
        global _monitoring_active
        _monitoring_active = True
    logger.info("Live monitoring started")


def stop_monitoring() -> None:
    with _lock:
        global _monitoring_active
        _monitoring_active = False
    CameraManager.reset()
    try:
        get_recognizer().reset_tracking()
    except RuntimeError:
        pass
    logger.info("Live monitoring stopped — camera released")


def generate_idle_mjpeg(
    settings: Settings,
    message: str,
    submessage: str = "",
    interval_seconds: float = 1.0,
):
    """MJPEG stream shown when monitoring is stopped."""
    quality = int(settings.performance_profile["jpeg_quality"])
    while True:
        frame = make_status_frame(message, submessage)
        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), quality],
        )
        if success:
            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(interval_seconds)
