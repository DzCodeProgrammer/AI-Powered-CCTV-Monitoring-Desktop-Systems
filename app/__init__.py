import os
import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from app.api.exceptions import sqlalchemy_exception_handler
from app.api.routes import auth, dashboard, health, model_settings, monitoring, registration
from app.database.connection import SessionLocal, init_db
from app.services.auth_service import ensure_default_admin
from app.services.background_tasks import maintenance_loop
from app.services.dahua_event_service import start_event_capture, stop_event_capture
from app.services.recognition_service import initialize_recognition
from app.services.monitoring_service import shutdown_monitoring
from app.services.schedule_service import apply_monitor_schedule
from app.utils.config import get_settings
from app.utils.logging import setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    for folder in [settings.dataset_dir, settings.screenshot_dir, settings.log_dir, "database"]:
        os.makedirs(folder, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        ensure_default_admin(db, settings)
        initialize_recognition(db, settings)
    finally:
        db.close()

    apply_monitor_schedule(get_settings())
    maintenance_task = asyncio.create_task(maintenance_loop())
    await start_event_capture()
    yield
    shutdown_monitoring()
    await stop_event_capture()
    maintenance_task.cancel()
    with suppress(asyncio.CancelledError):
        await maintenance_task


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=settings.session_max_age,
        same_site="lax",
        https_only=False,
    )

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(model_settings.router)
    app.include_router(registration.router)
    app.include_router(monitoring.router)

    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    return app
