from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database.connection import get_db
from app.services.model_settings_service import save_recognition_settings
from app.services.recognition_service import get_embedding_store, rebuild_embeddings
from app.utils.config import get_settings
from app.utils.templates import templates

router = APIRouter(tags=["Model Settings"])


@router.get("/dashboard/model-settings")
async def model_settings_page(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    settings = get_settings()
    store = get_embedding_store()
    registered_count = len(store.entries) if store else 0

    return templates.TemplateResponse(
        "dashboard/model_settings.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "admin": auth,
            "active_page": "model_settings",
            "face_model": settings.face_model,
            "recognition_threshold": settings.recognition_threshold,
            "recognition_margin": settings.recognition_margin,
            "recognition_interval": settings.recognition_interval,
            "registered_count": registered_count,
            "saved": request.query_params.get("saved") == "1",
            "rebuilt": request.query_params.get("rebuilt") == "1",
            "error": request.query_params.get("error", ""),
        },
    )


@router.post("/dashboard/model-settings")
async def model_settings_save(
    request: Request,
    recognition_threshold: float = Form(...),
    recognition_margin: float = Form(...),
    recognition_interval: float = Form(...),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    try:
        save_recognition_settings(
            recognition_threshold=recognition_threshold,
            recognition_margin=recognition_margin,
            recognition_interval=recognition_interval,
        )
        return RedirectResponse(url="/dashboard/model-settings?saved=1", status_code=303)
    except ValueError as exc:
        return RedirectResponse(
            url=f"/dashboard/model-settings?error={exc}",
            status_code=303,
        )
    except Exception:
        return RedirectResponse(
            url="/dashboard/model-settings?error=Could+not+save+settings",
            status_code=303,
        )


@router.post("/dashboard/model-settings/rebuild-embeddings")
async def model_settings_rebuild(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    rebuild_embeddings(db, get_settings())
    return RedirectResponse(url="/dashboard/model-settings?rebuilt=1", status_code=303)
