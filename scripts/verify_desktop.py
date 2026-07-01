"""Verify desktop app modules import (no GUI display)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except ImportError:
        print("SKIP: PySide6 not installed (pip install -r requirements-desktop.txt)")
        return 0

    from app.desktop.bootstrap import init_desktop_core
    from app.desktop.monitor_controller import resolve_camera_source
    from app.desktop.register_panel import RegisterPanel  # noqa: F401
    from app.desktop.model_settings_panel import ModelSettingsPanel  # noqa: F401
    from app.desktop.unknown_faces_panel import UnknownFacesPanel  # noqa: F401
    from app.desktop.system_tray import DesktopTray  # noqa: F401
    from app.utils.config import get_settings

    os.environ.setdefault("DESKTOP_MODE", "true")
    get_settings.cache_clear()
    init_desktop_core()
    settings = get_settings()
    if not settings.desktop_mode:
        print("WARN: DESKTOP_MODE not active")
    source = resolve_camera_source(settings)
    if not source:
        print("FAIL: camera source empty")
        return 1
    print(f"Desktop bootstrap OK, camera source configured")
    print("verify_desktop: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
