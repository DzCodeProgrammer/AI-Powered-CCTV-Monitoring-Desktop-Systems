"""Persist recognition tuning values to .env and reload runtime settings."""

from __future__ import annotations

import re
from pathlib import Path

from app.face_recognition.detector import FaceDetector
from app.services.recognition_service import get_recognizer
from app.utils.config import Settings, get_settings

_ENV_PATH = Path(".env")

_RECOGNITION_KEYS = {
    "RECOGNITION_THRESHOLD",
    "RECOGNITION_MARGIN",
    "RECOGNITION_INTERVAL",
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


def save_recognition_settings(
    *,
    recognition_threshold: float,
    recognition_margin: float,
    recognition_interval: float,
) -> Settings:
    if not 0.2 <= recognition_threshold <= 0.8:
        raise ValueError("Recognition threshold must be between 0.2 and 0.8.")
    if not 0.01 <= recognition_margin <= 0.25:
        raise ValueError("Recognition margin must be between 0.01 and 0.25.")
    if not 1.0 <= recognition_interval <= 300.0:
        raise ValueError("Recognition interval must be between 1 and 300 seconds.")

    update_env_file(
        {
            "RECOGNITION_THRESHOLD": f"{recognition_threshold:.2f}",
            "RECOGNITION_MARGIN": f"{recognition_margin:.2f}",
            "RECOGNITION_INTERVAL": f"{recognition_interval:.1f}".rstrip("0").rstrip("."),
        }
    )

    get_settings.cache_clear()
    settings = get_settings()
    apply_recognition_settings_to_runtime(settings)
    return settings


def apply_recognition_settings_to_runtime(settings: Settings) -> None:
    try:
        recognizer = get_recognizer()
    except RuntimeError:
        return

    recognizer.settings = settings
    recognizer.detector = FaceDetector(settings)
    recognizer._perf = settings.performance_profile
