from __future__ import annotations

import threading

from sqlalchemy.orm import Session

from app.face_recognition.embeddings import EmbeddingStore, ensure_embeddings
from app.face_recognition.recognizer import FaceRecognizer
from app.utils.config import Settings, get_settings
from app.utils.logging import get_logger

logger = get_logger("recognition")

_recognizer: FaceRecognizer | None = None
_embedding_store: EmbeddingStore | None = None


def get_embedding_store() -> EmbeddingStore | None:
    return _embedding_store


def _warmup_async(recognizer: FaceRecognizer) -> None:
    try:
        recognizer.warmup_model()
    except Exception as exc:
        logger.warning("Background DeepFace warmup failed: %s", exc)


def initialize_recognition(db: Session, settings: Settings | None = None) -> FaceRecognizer:
    global _recognizer, _embedding_store
    settings = settings or get_settings()
    _embedding_store = ensure_embeddings(db, settings)
    if _recognizer is None:
        _recognizer = FaceRecognizer(settings, _embedding_store)
        threading.Thread(
            target=_warmup_async,
            args=(_recognizer,),
            name="deepface-warmup",
            daemon=True,
        ).start()
    else:
        _recognizer.update_embeddings(_embedding_store)
        _recognizer.refresh_performance(settings)
    return _recognizer


def rebuild_embeddings(db: Session, settings: Settings | None = None) -> EmbeddingStore:
    global _recognizer, _embedding_store
    settings = settings or get_settings()
    _embedding_store = ensure_embeddings(db, settings, force=True)
    if _recognizer is None:
        _recognizer = FaceRecognizer(settings, _embedding_store)
    else:
        _recognizer.update_embeddings(_embedding_store)
        _recognizer.refresh_performance(settings)
    return _embedding_store


def get_recognizer() -> FaceRecognizer:
    if _recognizer is None:
        raise RuntimeError("Face recognition has not been initialized.")
    return _recognizer


def shutdown_recognition() -> None:
    global _recognizer
    if _recognizer is not None:
        _recognizer.shutdown(wait=False)
        _recognizer = None
