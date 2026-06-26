from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from deepface import DeepFace
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.registration_service import slugify_name
from app.utils.config import Settings
from app.utils.logging import get_logger, log_exception

TRAINING_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

logger = get_logger("face_recognition")


@dataclass
class EmbeddingEntry:
    user_id: int
    name: str
    embedding: np.ndarray


@dataclass
class EmbeddingStore:
    entries: list[EmbeddingEntry]

    @property
    def names(self) -> list[str]:
        return [entry.name for entry in self.entries]

    @property
    def vectors(self) -> np.ndarray:
        if not self.entries:
            return np.empty((0, 0))
        return np.vstack([entry.embedding for entry in self.entries])

    def is_empty(self) -> bool:
        return len(self.entries) == 0


def parse_embedding(vec) -> np.ndarray:
    if isinstance(vec, list) and len(vec) > 0:
        first = vec[0]
        if isinstance(first, dict) and "embedding" in first:
            return np.array(first["embedding"], dtype=float)
        return np.array(first, dtype=float)
    if isinstance(vec, dict) and "embedding" in vec:
        return np.array(vec["embedding"], dtype=float)
    return np.array(vec, dtype=float)


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(float)
    b = b.astype(float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - (np.dot(a, b) / (norm_a * norm_b))


def embeddings_cache_path(settings: Settings) -> Path:
    return Path("database") / "embeddings.pkl"


def _collect_training_images(user: User, settings: Settings) -> list[Path]:
    """Primary registration photo plus optional extra shots for averaging."""
    paths: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            return
        if path.suffix.lower() not in TRAINING_IMAGE_EXTENSIONS:
            return
        seen.add(resolved)
        paths.append(path)

    add(Path(user.image_path))

    slug = slugify_name(user.full_name)
    dataset_dir = Path(settings.dataset_dir)
    for candidate in sorted(dataset_dir.glob(f"{slug}_*")):
        add(candidate)

    training_dir = dataset_dir / "training" / str(user.id)
    if training_dir.is_dir():
        for candidate in sorted(training_dir.iterdir()):
            add(candidate)

    return paths


def _embed_image(image_path: Path, settings: Settings) -> np.ndarray:
    vector = DeepFace.represent(
        img_path=str(image_path),
        model_name=settings.face_model,
        enforce_detection=False,
        detector_backend="opencv",
    )
    embedding = parse_embedding(vector)
    if embedding.size == 0:
        raise ValueError(f"Empty embedding for {image_path}")
    return embedding


def _average_embeddings(vectors: list[np.ndarray]) -> np.ndarray:
    stacked = np.vstack(vectors)
    mean = stacked.mean(axis=0)
    norm = np.linalg.norm(mean)
    if norm == 0:
        return mean
    return mean / norm


def build_embeddings_from_db(db: Session, settings: Settings) -> EmbeddingStore:
    users = db.scalars(
        select(User).where(User.is_active.is_(True)).order_by(User.id)
    ).all()

    entries: list[EmbeddingEntry] = []
    missing_images: list[str] = []
    for user in users:
        training_images = _collect_training_images(user, settings)
        if not training_images:
            missing_images.append(f"{user.full_name} (id={user.id}): {user.image_path}")
            continue
        try:
            vectors = [_embed_image(image_path, settings) for image_path in training_images]
            embedding = (
                vectors[0] if len(vectors) == 1 else _average_embeddings(vectors)
            )
            if len(vectors) > 1:
                logger.info(
                    "Averaged %s training image(s) for %s (id=%s)",
                    len(vectors),
                    user.full_name,
                    user.id,
                )
            entries.append(
                EmbeddingEntry(user_id=user.id, name=user.full_name, embedding=embedding)
            )
            user.embedding_path = str(embeddings_cache_path(settings))
        except Exception as exc:
            log_exception(
                "face_recognition",
                f"Failed to build embedding for {user.full_name} (id={user.id})",
                exc,
            )
            continue

    for entry in missing_images:
        logger.warning("Missing face image: %s", entry)

    if missing_images:
        logger.warning(
            "Skipped %s user(s) with missing face images", len(missing_images)
        )

    db.commit()
    return EmbeddingStore(entries=entries)


def save_embedding_store(store: EmbeddingStore, settings: Settings) -> Path:
    cache_path = embeddings_cache_path(settings)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "entries": [
            {
                "user_id": entry.user_id,
                "name": entry.name,
                "embedding": entry.embedding,
            }
            for entry in store.entries
        ]
    }
    with cache_path.open("wb") as handle:
        pickle.dump(payload, handle)
    return cache_path


def load_embedding_store(settings: Settings) -> EmbeddingStore | None:
    cache_path = embeddings_cache_path(settings)
    if not cache_path.is_file():
        return None
    with cache_path.open("rb") as handle:
        payload = pickle.load(handle)
    entries = [
        EmbeddingEntry(
            user_id=item["user_id"],
            name=item["name"],
            embedding=np.array(item["embedding"], dtype=float),
        )
        for item in payload.get("entries", [])
    ]
    return EmbeddingStore(entries=entries)


def ensure_embeddings(db: Session, settings: Settings, force: bool = False) -> EmbeddingStore:
    if not force:
        cached = load_embedding_store(settings)
        if cached is not None and not cached.is_empty():
            return cached
    store = build_embeddings_from_db(db, settings)
    save_embedding_store(store, settings)
    return store
