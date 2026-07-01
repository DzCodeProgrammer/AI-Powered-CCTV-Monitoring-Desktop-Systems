from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.camera.manager import CameraManager
from app.camera.stream_broadcaster import LiveStreamBroadcaster
from app.database.connection import SessionLocal, get_db
from app.face_recognition.recognizer import STATUS_DETECTING, RecognitionEvent
from app.services.attendance_service import log_attendance
from app.services.detection_service import log_matches
from app.services.monitoring_service import (
    generate_idle_mjpeg,
    is_monitoring_active,
    shutdown_monitoring,
    start_monitoring,
    stop_monitoring,
)
from app.services.recognition_service import (
    get_embedding_store,
    get_recognizer,
)
from app.services.schedule_service import schedule_status
from app.utils.config import get_settings, mask_sensitive_url
from app.utils.templates import templates

router = APIRouter(tags=["Monitoring"])


def _default_camera_mode() -> str:
    return get_settings().camera_mode_label


def _active_camera_source(request: Request) -> str:
    settings = get_settings()
    session_source = request.session.get("camera_source")
    if isinstance(session_source, str) and session_source.strip():
        return session_source.strip()

    session_mode = request.session.get("camera_mode")
    if session_mode == "webcam":
        return request.session.get("webcam_index", settings.camera_source)
    if session_mode == "rtsp":
        return request.session.get("rtsp_url") or settings.rtsp_url
    if session_mode == "dahua":
        return settings.resolved_camera_source

    return settings.resolved_camera_source


def _safe_display_source(source: str) -> str:
    return mask_sensitive_url(source)


def _get_camera_manager(request: Request) -> CameraManager:
    settings = get_settings()
    source = _active_camera_source(request)
    return CameraManager.get_instance(settings, get_recognizer(), source)


@router.get("/dashboard/monitor")
async def monitor_page(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    settings = get_settings()
    store = get_embedding_store()
    registered_count = len(store.entries) if store else 0
    camera_source = _active_camera_source(request)
    camera_mode = request.session.get("camera_mode", _default_camera_mode())

    camera_connected = None
    monitoring_active = is_monitoring_active()
    if monitoring_active:
        broadcaster = LiveStreamBroadcaster.get()
        camera_connected = broadcaster.is_connected if broadcaster.is_running else None

    return templates.TemplateResponse(
        "dashboard/monitor.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "admin": auth,
            "active_page": "monitor",
            "registered_count": registered_count,
            "face_model": settings.face_model,
            "threshold": settings.recognition_threshold,
            "camera_source": _safe_display_source(camera_source),
            "camera_mode": camera_mode,
            "webcam_index": (
                settings.camera_source if settings.camera_source.isdigit() else "0"
            ),
            "rtsp_url": settings.rtsp_url or request.session.get("rtsp_url", ""),
            "dahua_host": settings.dahua_host,
            "dahua_username": settings.dahua_username,
            "attendance_interval": settings.attendance_interval,
            "camera_switched": request.query_params.get("camera") == "1",
            "monitoring_started": request.query_params.get("started") == "1",
            "monitoring_stopped": request.query_params.get("stopped") == "1",
            "camera_connected": camera_connected,
            "monitoring_active": monitoring_active,
            "performance": settings.performance_profile,
            "schedule_status": schedule_status(settings),
            "monitor_schedule_start": settings.monitor_schedule_start,
            "monitor_schedule_end": settings.monitor_schedule_end,
        },
    )


@router.post("/dashboard/monitor/camera")
async def switch_camera(
    request: Request,
    camera_mode: str = Form(...),
    webcam_index: str = Form("0"),
    rtsp_url: str = Form(""),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    settings = get_settings()

    if camera_mode == "dahua":
        if not settings.dahua_host:
            return RedirectResponse(url="/dashboard/monitor?error=dahua", status_code=303)
        source = settings.resolved_camera_source
        request.session["camera_mode"] = "dahua"
        request.session["camera_source"] = source
    elif camera_mode == "rtsp":
        source = rtsp_url.strip() or settings.rtsp_url.strip()
        if not source:
            return RedirectResponse(url="/dashboard/monitor?error=rtsp", status_code=303)
        request.session["camera_mode"] = "rtsp"
        request.session["camera_source"] = source
        request.session["rtsp_url"] = source
    else:
        source = webcam_index.strip() or "0"
        request.session["camera_mode"] = "webcam"
        request.session["camera_source"] = source
        request.session["webcam_index"] = source

    try:
        if is_monitoring_active():
            LiveStreamBroadcaster.reset()
            manager = CameraManager.switch_source(settings, get_recognizer(), source)
            get_recognizer().reset_tracking()
            if not manager.is_connected:
                return RedirectResponse(url="/dashboard/monitor?error=camera", status_code=303)
        else:
            CameraManager.reset()
            try:
                get_recognizer().reset_tracking()
            except RuntimeError:
                pass
    except ValueError:
        return RedirectResponse(url="/dashboard/monitor?error=camera", status_code=303)

    return RedirectResponse(url="/dashboard/monitor?camera=1", status_code=303)


@router.post("/dashboard/monitor/start")
async def start_monitoring_route(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    start_monitoring()
    return RedirectResponse(url="/dashboard/monitor?started=1", status_code=303)


@router.post("/dashboard/monitor/stop")
async def stop_monitoring_route(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    stop_monitoring()
    return RedirectResponse(url="/dashboard/monitor?stopped=1", status_code=303)


@router.get("/dashboard/monitor/feed")
async def monitor_feed(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    settings = get_settings()

    if not is_monitoring_active():
        return StreamingResponse(
            generate_idle_mjpeg(
                settings,
                "Monitoring stopped",
                "Click Start monitoring to resume live CCTV.",
            ),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    camera_source = _active_camera_source(request)
    broadcaster = LiveStreamBroadcaster.get()

    def generate():
        session = SessionLocal()
        try:
            def on_recognition(event: RecognitionEvent):
                if event.match.status == STATUS_DETECTING:
                    return
                current_settings = get_settings()
                log_matches(
                    session,
                    current_settings,
                    event.annotated_frame,
                    [event.match],
                    camera_source,
                )
                log_attendance(session, current_settings, [event.match], camera_source)

            broadcaster.ensure_running(
                settings,
                get_recognizer(),
                camera_source,
                on_recognition=on_recognition,
            )
            for chunk in broadcaster.iter_mjpeg():
                yield chunk
        finally:
            session.close()

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
