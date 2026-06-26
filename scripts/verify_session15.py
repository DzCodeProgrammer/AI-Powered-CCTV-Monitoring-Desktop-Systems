"""Verify Session 15: final deliverables checklist."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DELIVERABLES = {
    "README.md": ["Quick Start", "Documentation", "Tech Stack"],
    "requirements.txt": ["fastapi", "openpyxl", "sqlalchemy", "deepface"],
    "scripts/schema.sql": ["CREATE TABLE", "users", "attendance_logs", "unknown_faces"],
    "scripts/init_mysql.sql": ["CREATE DATABASE", "GRANT"],
    "docs/INSTALLATION.md": ["Prerequisites", "Clone"],
    "docs/PROJECT_STRUCTURE.md": ["Directory Tree", "Architecture"],
    "docs/DATABASE.md": ["Schema", "users"],
    "docs/API.md": ["/api/health", "attendance/export"],
    "docs/DEPLOYMENT.md": ["Production", "Nginx"],
    "docs/DELIVERABLES.md": ["Deliverables", "Folder Structure"],
    "main.py": ["create_app"],
    "docker-compose.yml": ["mysql"],
    "LICENSE": ["MIT"],
}

APP_MODULES = [
    "app/__init__.py",
    "app/api/routes/dashboard.py",
    "app/api/routes/monitoring.py",
    "app/api/routes/registration.py",
    "app/api/routes/auth.py",
    "app/services/export_service.py",
    "app/face_recognition/recognizer.py",
    "app/camera/manager.py",
]


def main() -> int:
    missing: list[str] = []
    incomplete: list[str] = []

    for rel_path, keywords in DELIVERABLES.items():
        path = PROJECT_ROOT / rel_path
        if not path.is_file():
            missing.append(rel_path)
            continue
        content = path.read_text(encoding="utf-8").lower()
        for keyword in keywords:
            if keyword.lower() not in content:
                incomplete.append(f"{rel_path}: missing '{keyword}'")

    for rel_path in APP_MODULES:
        if not (PROJECT_ROOT / rel_path).is_file():
            missing.append(rel_path)

    if missing:
        print("FAIL: missing deliverable files:")
        for item in missing:
            print(f"  - {item}")
        return 1

    if incomplete:
        print("FAIL: incomplete deliverables:")
        for item in incomplete:
            print(f"  - {item}")
        return 1

    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    for doc in [
        "docs/INSTALLATION.md",
        "docs/DELIVERABLES.md",
        "scripts/schema.sql",
    ]:
        if doc not in readme:
            print(f"FAIL: README.md missing link/reference to {doc}")
            return 1

    print(f"Deliverable files: {len(DELIVERABLES)} OK")
    print(f"Core app modules: {len(APP_MODULES)} OK")
    print("Session 15 deliverables verification: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
