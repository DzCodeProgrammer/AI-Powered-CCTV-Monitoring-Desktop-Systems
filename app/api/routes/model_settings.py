from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_admin_from_session, require_admin
from app.database.connection import get_db
from app.services.cleanup_service import run_cleanup
from app.services.model_settings_service import (
    apply_laptop_8gb_preset,
    save_camera_settings,
    save_model_settings,
    save_notification_settings,
    save_operations_settings,
    form_bool,
)
from app.services.recognition_service import get_embedding_store, rebuild_embeddings
from app.services.schedule_service import schedule_status
from app.services.system_metrics import system_metrics_payload
from app.services.whatsapp_service import send_test_message
from app.utils.config import get_settings
from app.utils.templates import templates

router = APIRouter(tags=["Model Settings"])


@router.get("/api/system/metrics")
async def system_metrics_api(request: Request, db: Session = Depends(get_db)):
    if not get_admin_from_session(request, db):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return system_metrics_payload()


@router.get("/dashboard/model-settings")
async def model_settings_page(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    settings = get_settings()
    store = get_embedding_store()
    registered_count = len(store.entries) if store else 0
    sched = schedule_status(settings)

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
            "frame_skip": settings.frame_skip,
            "process_max_width": settings.process_max_width,
            "max_faces_per_frame": settings.max_faces_per_frame,
            "low_end_mode": settings.low_end_mode,
            "registered_count": registered_count,
            "monitor_schedule_enabled": settings.monitor_schedule_enabled,
            "monitor_schedule_start": settings.monitor_schedule_start,
            "monitor_schedule_end": settings.monitor_schedule_end,
            "cleanup_enabled": settings.cleanup_enabled,
            "log_retention_days": settings.log_retention_days,
            "screenshot_retention_days": settings.screenshot_retention_days,
            "cleanup_interval_hours": settings.cleanup_interval_hours,
            "schedule_status": sched,
            "wa_notify_enabled": settings.wa_notify_enabled,
            "wa_admin_phones": settings.wa_admin_phones,
            "wa_notify_unknown": settings.wa_notify_unknown,
            "wa_notify_attendance": settings.wa_notify_attendance,
            "wa_token_configured": bool(settings.wa_api_token.strip()),
            "dahua_subtype": settings.dahua_subtype,
            "camera_mode": settings.camera_mode_label,
            "saved": request.query_params.get("saved") == "1",
            "ops_saved": request.query_params.get("ops_saved") == "1",
            "notif_saved": request.query_params.get("notif_saved") == "1",
            "camera_saved": request.query_params.get("camera_saved") == "1",
            "wa_test_ok": request.query_params.get("wa_test") == "ok",
            "wa_test_msg": request.query_params.get("wa_msg", ""),
            "rebuilt": request.query_params.get("rebuilt") == "1",
            "cleanup_done": request.query_params.get("cleanup") == "1",
            "preset_applied": request.query_params.get("preset") == "1",
            "error": request.query_params.get("error", ""),
        },
    )


@router.post("/dashboard/model-settings")
async def model_settings_save(
    request: Request,
    recognition_threshold: float = Form(...),
    recognition_margin: float = Form(...),
    recognition_interval: float = Form(...),
    frame_skip: int = Form(...),
    process_max_width: int = Form(...),
    max_faces_per_frame: int = Form(...),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    try:
        save_model_settings(
            recognition_threshold=recognition_threshold,
            recognition_margin=recognition_margin,
            recognition_interval=recognition_interval,
            frame_skip=frame_skip,
            process_max_width=process_max_width,
            max_faces_per_frame=max_faces_per_frame,
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


@router.post("/dashboard/model-settings/preset/laptop-8gb")
async def model_settings_laptop_preset(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    try:
        apply_laptop_8gb_preset()
        return RedirectResponse(url="/dashboard/model-settings?preset=1", status_code=303)
    except Exception:
        return RedirectResponse(
            url="/dashboard/model-settings?error=Could+not+apply+preset",
            status_code=303,
        )


@router.post("/dashboard/model-settings/operations")
async def model_settings_operations(
    request: Request,
    monitor_schedule_enabled: str = Form(""),
    monitor_schedule_start: str = Form("07:00"),
    monitor_schedule_end: str = Form("17:00"),
    cleanup_enabled: str = Form(""),
    log_retention_days: int = Form(30),
    screenshot_retention_days: int = Form(14),
    cleanup_interval_hours: int = Form(24),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    try:
        save_operations_settings(
            monitor_schedule_enabled=form_bool(monitor_schedule_enabled),
            monitor_schedule_start=monitor_schedule_start,
            monitor_schedule_end=monitor_schedule_end,
            cleanup_enabled=form_bool(cleanup_enabled),
            log_retention_days=log_retention_days,
            screenshot_retention_days=screenshot_retention_days,
            cleanup_interval_hours=cleanup_interval_hours,
        )
        return RedirectResponse(url="/dashboard/model-settings?ops_saved=1", status_code=303)
    except ValueError as exc:
        return RedirectResponse(
            url=f"/dashboard/model-settings?error={exc}",
            status_code=303,
        )
    except Exception:
        return RedirectResponse(
            url="/dashboard/model-settings?error=Could+not+save+operations+settings",
            status_code=303,
        )


@router.post("/dashboard/model-settings/run-cleanup")
async def model_settings_run_cleanup(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    run_cleanup(get_settings())
    return RedirectResponse(url="/dashboard/model-settings?cleanup=1", status_code=303)


@router.post("/dashboard/model-settings/notifications")
async def model_settings_notifications(
    request: Request,
    wa_notify_enabled: str = Form(""),
    wa_api_token: str = Form(""),
    wa_admin_phones: str = Form(""),
    wa_notify_unknown: str = Form(""),
    wa_notify_attendance: str = Form(""),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    current = get_settings()
    token = wa_api_token.strip() or current.wa_api_token

    try:
        save_notification_settings(
            wa_notify_enabled=form_bool(wa_notify_enabled),
            wa_api_token=token,
            wa_admin_phones=wa_admin_phones,
            wa_notify_unknown=form_bool(wa_notify_unknown),
            wa_notify_attendance=form_bool(wa_notify_attendance),
        )
        return RedirectResponse(url="/dashboard/model-settings?notif_saved=1", status_code=303)
    except ValueError as exc:
        return RedirectResponse(
            url=f"/dashboard/model-settings?error={exc}",
            status_code=303,
        )
    except Exception:
        return RedirectResponse(
            url="/dashboard/model-settings?error=Could+not+save+notification+settings",
            status_code=303,
        )


@router.post("/dashboard/model-settings/test-wa")
async def model_settings_test_wa(
    request: Request,
    wa_test_phone: str = Form(...),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    ok, message = send_test_message(get_settings(), wa_test_phone)
    param = "ok" if ok else "fail"
    from urllib.parse import quote

    return RedirectResponse(
        url=f"/dashboard/model-settings?wa_test={param}&wa_msg={quote(message)}",
        status_code=303,
    )


@router.post("/dashboard/model-settings/camera")
async def model_settings_camera(
    request: Request,
    dahua_subtype: int = Form(1),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    try:
        save_camera_settings(dahua_subtype=dahua_subtype)
        return RedirectResponse(url="/dashboard/model-settings?camera_saved=1", status_code=303)
    except ValueError as exc:
        return RedirectResponse(
            url=f"/dashboard/model-settings?error={exc}",
            status_code=303,
        )
    except Exception:
        return RedirectResponse(
            url="/dashboard/model-settings?error=Could+not+save+camera+settings",
            status_code=303,
        )


@router.post("/dashboard/model-settings/rebuild-embeddings")
async def model_settings_rebuild(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    rebuild_embeddings(db, get_settings())
    return RedirectResponse(url="/dashboard/model-settings?rebuilt=1", status_code=303)
