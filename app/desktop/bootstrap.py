"""Initialize core services for desktop mode (no FastAPI / browser)."""

from __future__ import annotations

import os

from app.database.connection import SessionLocal, init_db
from app.services.auth_service import ensure_default_admin
from app.services.recognition_service import initialize_recognition
from app.utils.config import get_settings
from app.utils.logging import setup_logging


def init_desktop_core() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    setup_logging()
    if settings.desktop_mode:
        from app.utils.logging import get_logger

        get_logger("desktop").info(
            "Desktop mode active — cctv_mode=%s display_max=%spx",
            settings.cctv_mode,
            settings.desktop_display_max_width,
        )
    for folder in [settings.dataset_dir, settings.screenshot_dir, settings.log_dir, "database"]:
        os.makedirs(folder, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        ensure_default_admin(db, settings)
        initialize_recognition(db, settings)
    finally:
        db.close()
