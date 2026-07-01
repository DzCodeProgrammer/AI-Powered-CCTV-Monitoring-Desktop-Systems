# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Smart CCTV Desktop.

Build (from project root, venv active):
  python -m PyInstaller smart_cctv_desktop.spec --clean
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH)

# Qt / PySide6 — required for native desktop UI (DLLs + plugins)
pyside6_datas, pyside6_binaries, pyside6_hidden = collect_all("PySide6")

# OpenCV — needs its data files (haarcascade_*.xml) at runtime
cv2_datas, cv2_binaries, cv2_hidden = collect_all("cv2")

# App package tree
app_hidden = collect_submodules("app")

a = Analysis(
    [str(ROOT / "desktop_main.py")],
    pathex=[str(ROOT)],
    binaries=pyside6_binaries + cv2_binaries,
    datas=[(str(ROOT / ".env.example"), ".")] + pyside6_datas + cv2_datas,
    hiddenimports=[
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "cv2",
        "numpy",
        "sqlalchemy",
        "pymysql",
        "passlib.handlers.bcrypt",
        "tensorflow",
        "tf_keras",
        "deepface",
    ]
    + pyside6_hidden
    + cv2_hidden
    + app_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SmartCCTV",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SmartCCTV",
)
