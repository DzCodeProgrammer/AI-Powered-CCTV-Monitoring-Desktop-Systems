import io
import re
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.whatsapp_service import normalize_wa_phone
from app.utils.config import Settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_EXTRA_IMAGES = 5


class RegistrationError(Exception):
    pass


def slugify_name(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"[\s_-]+", "_", cleaned)
    return cleaned.lower() or "person"


def validate_image_file(file: UploadFile, content: bytes) -> str:
    if not file.filename:
        raise RegistrationError("Image file is required.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise RegistrationError("Allowed formats: JPG, JPEG, PNG, WEBP.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise RegistrationError("Image must be 5 MB or smaller.")

    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except Exception as exc:
        raise RegistrationError("Invalid image file.") from exc

    return ext


def get_user_by_name(db: Session, name: str) -> User | None:
    return db.scalar(select(User).where(User.full_name == name))


def training_dir_for_user(settings: Settings, user_id: int) -> Path:
    return Path(settings.dataset_dir) / "training" / str(user_id)


def _write_dataset_image(
    settings: Settings,
    slug: str,
    ext: str,
    content: bytes,
    *,
    suffix: str = "",
) -> Path:
    dataset_dir = Path(settings.dataset_dir)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{slug}_{timestamp}{suffix}{ext}"
    file_path = dataset_dir / filename
    file_path.write_bytes(content)
    return file_path


def save_extra_training_images(
    settings: Settings,
    user_id: int,
    images: list[tuple[UploadFile, bytes]],
) -> int:
    if not images:
        return 0

    training_dir = training_dir_for_user(settings, user_id)
    training_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for index, (file, content) in enumerate(images):
        ext = validate_image_file(file, content)
        filename = f"extra_{timestamp}_{index}{ext}"
        (training_dir / filename).write_bytes(content)
        saved += 1

    return saved


def validate_phone_number(phone: str | None) -> str | None:
    if phone is None or not str(phone).strip():
        return None
    normalized = normalize_wa_phone(str(phone).strip())
    if not normalized:
        raise RegistrationError(
            "Invalid WhatsApp number. Use format 628123456789 or 08123456789."
        )
    return normalized


def register_person(
    db: Session,
    settings: Settings,
    name: str,
    file: UploadFile,
    content: bytes,
    phone_number: str | None = None,
) -> User:
    name = name.strip()
    if not name:
        raise RegistrationError("Person name is required.")
    if len(name) > 100:
        raise RegistrationError("Name must be 100 characters or fewer.")

    if get_user_by_name(db, name):
        raise RegistrationError(f"A person named '{name}' is already registered.")

    ext = validate_image_file(file, content)
    slug = slugify_name(name)
    file_path = _write_dataset_image(settings, slug, ext, content)
    relative_path = str(file_path).replace("\\", "/")
    phone = validate_phone_number(phone_number)

    user = User(
        full_name=name,
        image_path=relative_path,
        is_active=True,
        phone_number=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_person_with_extras(
    db: Session,
    settings: Settings,
    name: str,
    primary_file: UploadFile,
    primary_content: bytes,
    extra_images: list[tuple[UploadFile, bytes]],
    phone_number: str | None = None,
) -> User:
    if len(extra_images) > MAX_EXTRA_IMAGES:
        raise RegistrationError(
            f"You can upload at most {MAX_EXTRA_IMAGES} extra training photos."
        )

    user = register_person(
        db, settings, name, primary_file, primary_content, phone_number=phone_number
    )
    save_extra_training_images(settings, user.id, extra_images)
    return user


def register_person_from_image_file(
    db: Session,
    settings: Settings,
    name: str,
    source_path: Path,
    phone_number: str | None = None,
) -> User:
    name = name.strip()
    if not name:
        raise RegistrationError("Person name is required.")
    if len(name) > 100:
        raise RegistrationError("Name must be 100 characters or fewer.")
    if get_user_by_name(db, name):
        raise RegistrationError(f"A person named '{name}' is already registered.")
    if not source_path.is_file():
        raise RegistrationError("Source face image was not found.")

    ext = source_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise RegistrationError("Allowed formats: JPG, JPEG, PNG, WEBP.")

    content = source_path.read_bytes()
    if len(content) > MAX_UPLOAD_BYTES:
        raise RegistrationError("Image must be 5 MB or smaller.")

    slug = slugify_name(name)
    file_path = _write_dataset_image(settings, slug, ext, content, suffix="_from_unknown")
    relative_path = str(file_path).replace("\\", "/")
    phone = validate_phone_number(phone_number)

    user = User(
        full_name=name,
        image_path=relative_path,
        is_active=True,
        phone_number=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    training_dir = training_dir_for_user(settings, user.id)
    training_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, training_dir / f"source_unknown{ext}")
    return user
