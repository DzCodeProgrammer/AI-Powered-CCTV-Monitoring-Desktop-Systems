"""Registered user management — delete resigned users and refresh embeddings."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.database.errors import safe_commit
from app.models.user import User
from app.services.monitoring_service import stop_monitoring
from app.services.recognition_service import rebuild_embeddings
from app.utils.config import Settings
from app.utils.logging import get_logger

logger = get_logger("users")


def _resolve_dataset_path(stored_path: str) -> Path | None:
    path = Path(stored_path)
    if path.is_file():
        return path
    alt = Path.cwd() / stored_path
    if alt.is_file():
        return alt
    return None


def _remove_dataset_image(stored_path: str) -> None:
    file_path = _resolve_dataset_path(stored_path)
    if file_path is None:
        return
    try:
        file_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Could not delete dataset image %s: %s", stored_path, exc)


def _remove_training_dir(settings: Settings, user_id: int) -> None:
    training_dir = Path(settings.dataset_dir) / "training" / str(user_id)
    if not training_dir.is_dir():
        return
    for path in training_dir.iterdir():
        try:
            if path.is_file():
                path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Could not delete training file %s: %s", path, exc)
    try:
        training_dir.rmdir()
    except OSError:
        pass


def delete_user(db: Session, user_id: int, settings: Settings) -> bool:
    user = db.get(User, user_id)
    if user is None:
        return False

    stop_monitoring()

    image_path = user.image_path
    name = user.full_name
    db.delete(user)
    if not safe_commit(db, f"delete user {user_id} ({name})"):
        return False

    _remove_dataset_image(image_path)
    _remove_training_dir(settings, user_id)
    rebuild_embeddings(db, settings)
    logger.info("Deleted user %s (id=%s) and rebuilt embeddings", name, user_id)
    return True
