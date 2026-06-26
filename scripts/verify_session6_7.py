"""Verify Session 6 & 7: dashboard stats and unknown face gallery."""

import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app import create_app
from app.database.connection import SessionLocal, init_db
from app.face_recognition.recognizer import STATUS_UNKNOWN, FaceMatch
from app.models.detection import Detection
from app.models.unknown_face import UnknownFace
from app.models.user import User
from app.services.auth_service import create_admin, get_admin_by_username
from app.services.dashboard_service import get_dashboard_stats
from app.services.detection_service import log_matches
from app.utils.config import get_settings


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    init_db()

    admin_user = "_verify_s67_admin_"
    db = SessionLocal()
    try:
        admin = get_admin_by_username(db, admin_user)
        if admin:
            db.delete(admin)
        db.execute(delete(UnknownFace))
        db.execute(delete(Detection))
        db.execute(delete(User).where(User.full_name == "_Verify S67_"))
        db.commit()
        create_admin(db, admin_user, "verify-s67-pass-123")
        db.add(User(full_name="_Verify S67_", image_path="datasets/x.jpg", is_active=True))
        db.commit()
    finally:
        db.close()

    stats = get_dashboard_stats(SessionLocal())
    if stats.registered_users < 1:
        print("FAIL: registered users stat")
        return 1

    unknown_dir = Path(settings.screenshot_dir) / "unknown"
    unknown_dir.mkdir(parents=True, exist_ok=True)
    shot = unknown_dir / "test_unknown.jpg"
    fake_crop = np.zeros((80, 80, 3), dtype=np.uint8)
    import cv2

    cv2.imwrite(str(shot), fake_crop)
    rel_path = f"{settings.screenshot_dir}/unknown/test_unknown.jpg"

    db = SessionLocal()
    try:
        db.add(
            UnknownFace(
                image_path=rel_path,
                camera_source="0",
                notes="verify",
            )
        )
        db.commit()

        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        match = FaceMatch(
            name="Unknown",
            status=STATUS_UNKNOWN,
            confidence=0.2,
            user_id=None,
            bbox=(50, 50, 80, 80),
        )
        log_matches(db, settings, frame, [match], camera_source="0")

        unknown_count = db.scalar(
            select(func.count()).select_from(UnknownFace)
        ) or 0
        if unknown_count < 2:
            print("FAIL: unknown face records not saved")
            return 1

        stats = get_dashboard_stats(db)
        if stats.unknown_faces_total < 1:
            print("FAIL: unknown_faces_total stat")
            return 1
    finally:
        db.close()

    app = create_app()
    client = TestClient(app)
    client.post("/login", data={"username": admin_user, "password": "verify-s67-pass-123"})

    response = client.get("/dashboard")
    if response.status_code != 200:
        print(f"FAIL: dashboard returned {response.status_code}")
        return 1
    if "Today's Detections" not in response.text:
        print("FAIL: dashboard missing today's detections section")
        return 1
    if "Attendance Statistics" not in response.text:
        print("FAIL: dashboard missing attendance statistics")
        return 1

    response = client.get("/dashboard/unknown-faces")
    if response.status_code != 200:
        print(f"FAIL: unknown gallery returned {response.status_code}")
        return 1
    if "Unknown Face Gallery" not in response.text:
        print("FAIL: unknown gallery page content missing")
        return 1

    response = client.get("/dashboard/unknown-faces/1/image")
    if response.status_code not in (200, 303):
        print(f"FAIL: unknown image route returned {response.status_code}")
        return 1

    db = SessionLocal()
    try:
        admin = get_admin_by_username(db, admin_user)
        if admin:
            db.delete(admin)
        db.execute(delete(UnknownFace))
        db.execute(delete(Detection))
        db.execute(delete(User).where(User.full_name == "_Verify S67_"))
        db.commit()
    finally:
        db.close()
    if shot.is_file():
        shot.unlink()

    print("Session 6 & 7 verification: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
