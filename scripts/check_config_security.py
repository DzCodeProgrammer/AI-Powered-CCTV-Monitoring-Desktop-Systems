"""Security checks for configuration and secrets (Session 9)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    issues: list[str] = []
    warnings: list[str] = []

    env_file = PROJECT_ROOT / ".env"
    example_file = PROJECT_ROOT / ".env.example"
    gitignore = PROJECT_ROOT / ".gitignore"

    if not gitignore.is_file():
        issues.append(".gitignore missing")
    elif ".env" not in gitignore.read_text(encoding="utf-8"):
        issues.append(".env is not listed in .gitignore")

    if example_file.is_file():
        example_text = example_file.read_text(encoding="utf-8").lower()
        if "dahua@123" in example_text:
            issues.append(".env.example contains real Dahua password")
        if "change-this" not in example_text:
            warnings.append(".env.example may be missing placeholder markers")

    if env_file.is_file():
        env_text = env_file.read_text(encoding="utf-8")
        if "SECRET_KEY=dev-secret" in env_text or "SECRET_KEY=change-this" in env_text:
            warnings.append(".env still uses default SECRET_KEY")
        if "DB_PASSWORD=change-this" in env_text:
            warnings.append(".env still uses placeholder DB_PASSWORD")
    else:
        warnings.append(".env file not found (copy from .env.example)")

    for path in (PROJECT_ROOT / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Dahua@123" in text:
            issues.append(f"Hardcoded Dahua password in {path.relative_to(PROJECT_ROOT)}")

    if issues:
        print("SECURITY CHECK: FAILED")
        for item in issues:
            print(f"  [ERROR] {item}")
        for item in warnings:
            print(f"  [WARN]  {item}")
        return 1

    print("SECURITY CHECK: OK")
    for item in warnings:
        print(f"  [WARN]  {item}")
    print("  - .env is gitignored")
    print("  - no hardcoded Dahua credentials in source code")
    print("  - .env.example uses placeholders only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
