from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database.connection import get_db
from app.models.unknown_face import UnknownFace
from app.services.recognition_service import rebuild_embeddings
from app.services.registration_service import (
    MAX_EXTRA_IMAGES,
    RegistrationError,
    register_person_from_image_file,
    register_person_with_extras,
)
from app.services.unknown_face_service import delete_unknown_face
from app.utils.config import get_settings
from app.utils.logging import log_exception
from app.utils.templates import templates

router = APIRouter(tags=["Registration"])
settings = get_settings()


def _resolve_image_path(stored_path: str) -> Path | None:
    path = Path(stored_path)
    if path.is_file():
        return path
    alt = Path.cwd() / stored_path
    if alt.is_file():
        return alt
    return None


async def _read_uploads_async(files: list[UploadFile]) -> list[tuple[UploadFile, bytes]]:
    pairs: list[tuple[UploadFile, bytes]] = []
    for file in files:
        if not file.filename:
            continue
        content = await file.read()
        pairs.append((file, content))
    return pairs


@router.get("/dashboard/register")
async def register_page(request: Request, db: Session = Depends(get_db)):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    return templates.TemplateResponse(
        "dashboard/register.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "admin": auth,
            "active_page": "register",
            "error": None,
            "success": None,
            "name": "",
            "max_extra_images": MAX_EXTRA_IMAGES,
        },
    )


@router.post("/dashboard/register")
async def register_submit(
    request: Request,
    name: str = Form(...),
    phone_number: str = Form(""),
    image: UploadFile = File(...),
    extra_images: Annotated[list[UploadFile], File()] = [],
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    context = {
        "request": request,
        "app_name": settings.app_name,
        "admin": auth,
        "active_page": "register",
        "error": None,
        "success": None,
        "name": name.strip(),
        "max_extra_images": MAX_EXTRA_IMAGES,
    }

    try:
        primary_content = await image.read()
        extras = await _read_uploads_async(extra_images)
        user = register_person_with_extras(
            db, settings, name, image, primary_content, extras,
            phone_number=phone_number.strip() or None,
        )
        rebuild_embeddings(db, settings)
        extra_q = f"&extras={len(extras)}" if extras else ""
        return RedirectResponse(
            url=f"/dashboard/users?registered={user.id}{extra_q}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except RegistrationError as exc:
        context["error"] = str(exc)
        return templates.TemplateResponse(
            "dashboard/register.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except OperationalError as exc:
        log_exception("registration", "Registration failed (database schema)", exc)
        if "Unknown column" in str(exc):
            context["error"] = (
                "Database schema is outdated. Stop the app, run "
                "python scripts\\migrate_schema.py, then restart and try again."
            )
        else:
            context["error"] = "Database error during registration. Check logs/errors.log."
        return templates.TemplateResponse(
            "dashboard/register.html",
            context,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as exc:
        log_exception("registration", "Registration failed", exc)
        context["error"] = "Registration failed. Please try again."
        return templates.TemplateResponse(
            "dashboard/register.html",
            context,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/dashboard/unknown-faces/{face_id}/register")
async def register_from_unknown_face(
    face_id: int,
    request: Request,
    name: str = Form(...),
    phone_number: str = Form(""),
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    face = db.get(UnknownFace, face_id)
    if face is None:
        return RedirectResponse(
            url="/dashboard/unknown-faces?error=not_found",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    source_path = _resolve_image_path(face.image_path)
    if source_path is None:
        return RedirectResponse(
            url="/dashboard/unknown-faces?error=image_missing",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        user = register_person_from_image_file(
            db, settings, name, source_path,
            phone_number=phone_number.strip() or None,
        )
        rebuild_embeddings(db, settings)
        delete_unknown_face(db, face_id)
        return RedirectResponse(
            url=f"/dashboard/users?registered={user.id}&from_unknown=1",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except RegistrationError as exc:
        return RedirectResponse(
            url=f"/dashboard/unknown-faces?error=register&msg={exc}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as exc:
        log_exception("registration", "Register from unknown face failed", exc)
        return RedirectResponse(
            url="/dashboard/unknown-faces?error=register",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.get("/dashboard/datasets/{filename}")
async def serve_dataset_image(
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
):
    auth = require_admin(request, db)
    if isinstance(auth, RedirectResponse):
        return auth

    safe_name = filename.replace("\\", "/").split("/")[-1]
    file_path = Path(settings.dataset_dir) / safe_name
    if not file_path.is_file():
        return RedirectResponse(url="/dashboard/users", status_code=303)

    return FileResponse(file_path)
