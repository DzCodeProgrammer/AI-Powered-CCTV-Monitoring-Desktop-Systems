import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import health
from app.database.connection import init_db
from app.utils.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    for folder in [settings.dataset_dir, settings.screenshot_dir, settings.log_dir, "database"]:
        os.makedirs(folder, exist_ok=True)
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(health.router, prefix="/api")

    return app
