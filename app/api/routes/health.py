from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.dahua_event_service import event_capture_should_run, get_event_status
from app.utils.config import get_settings
from app.utils.logging import log_exception

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    settings = get_settings()
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        log_exception("database", "Health check database query failed", exc)

    event_status = get_event_status()
    event_block = {
        "enabled": event_capture_should_run(settings),
        "cctv_mode": settings.cctv_mode,
        "connected": event_status.connected,
        "events_processed": event_status.events_processed,
        "last_event_at": (
            event_status.last_event_at.isoformat() if event_status.last_event_at else None
        ),
        "last_error": event_status.last_error,
    }

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": settings.app_name,
        "environment": settings.app_env,
        "database": db_status,
        "db_driver": settings.db_driver,
        "db_host": settings.db_host,
        "db_name": settings.db_name,
        "camera_mode": settings.camera_mode_label,
        "camera_source": settings.safe_camera_display,
        "performance": settings.performance_profile,
        "dahua_events": event_block,
    }
