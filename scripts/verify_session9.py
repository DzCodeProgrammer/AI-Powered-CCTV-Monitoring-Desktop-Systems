"""Verify Session 9: configuration and Dahua RTSP builder."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from app.utils.config import get_settings, mask_sensitive_url


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()

    required = {
        "DB_HOST": settings.db_host,
        "DB_PORT": str(settings.db_port),
        "DB_USER": settings.db_user,
        "DB_PASSWORD": settings.db_password,
        "DB_NAME": settings.db_name,
    }
    missing = [key for key, value in required.items() if not str(value).strip()]
    if missing:
        print(f"FAIL: missing config for {', '.join(missing)}")
        return 1

    if settings.camera_mode_label == "dahua":
        rtsp = settings.resolved_camera_source
        if not rtsp.startswith("rtsp://"):
            print("FAIL: Dahua mode must produce RTSP URL")
            return 1
        masked = mask_sensitive_url(rtsp)
        if settings.dahua_password and settings.dahua_password in masked:
            print("FAIL: password visible in masked URL")
            return 1
        print(f"Dahua RTSP (masked): {masked}")
    else:
        print(f"Camera mode: {settings.camera_mode_label}")

    safe = settings.safe_camera_display
    if settings.dahua_password and settings.dahua_password in safe:
        print("FAIL: password exposed in safe_camera_display")
        return 1

    print("Session 9 configuration verification: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
