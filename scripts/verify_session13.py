"""Verify Session 13: code quality (type hints, PEP8 config, modular layout)."""

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PACKAGES = [
    "app/api/routes",
    "app/services",
    "app/models",
    "app/face_recognition",
    "app/database",
    "app/camera",
    "app/utils",
]

FUTURE_ANNOTATIONS_FILES = [
    "app/api/routes/dashboard.py",
    "app/api/exceptions.py",
    "app/services/export_service.py",
    "app/models/unknown_face.py",
    "app/face_recognition/detector.py",
    "app/face_recognition/recognizer.py",
    "app/database/migrate.py",
]


def main() -> int:
    missing_dirs = [p for p in REQUIRED_PACKAGES if not (PROJECT_ROOT / p).is_dir()]
    if missing_dirs:
        print("FAIL: missing package directories:")
        for path in missing_dirs:
            print(f"  - {path}")
        return 1
    print(f"Modular packages: {len(REQUIRED_PACKAGES)} OK")

    if not (PROJECT_ROOT / "pyproject.toml").is_file():
        print("FAIL: pyproject.toml (Ruff/PEP8 config) missing")
        return 1
    print("PEP8 config (pyproject.toml): OK")

    for rel in FUTURE_ANNOTATIONS_FILES:
        path = PROJECT_ROOT / rel
        if not path.is_file():
            print(f"FAIL: missing {rel}")
            return 1
        first_line = path.read_text(encoding="utf-8").splitlines()[:1]
        if "from __future__ import annotations" not in first_line[0]:
            print(f"FAIL: {rel} missing future annotations")
            return 1
    print("Type hint style (future annotations): OK")

    dashboard_path = PROJECT_ROOT / "app/api/routes/dashboard.py"
    tree = ast.parse(dashboard_path.read_text(encoding="utf-8"))
    func_defs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    typed_returns = sum(1 for fn in func_defs if fn.returns is not None)
    if typed_returns < 1:
        print("FAIL: dashboard routes should include return type hints")
        return 1
    print(f"Route return type hints: {typed_returns} function(s)")

    exceptions = (PROJECT_ROOT / "app/api/exceptions.py").read_text(encoding="utf-8")
    if "RedirectResponse" not in exceptions or "_wants_html" not in exceptions:
        print("FAIL: HTML-aware database exception handler missing")
        return 1
    print("HTML-aware error handler: OK")

    print("Session 13 code quality verification: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
