"""Migrate MySQL schema from early sessions to current models."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    from app.database.connection import engine, init_db
    from app.database.migrate import run_migrations
    from app.utils.config import get_settings

    settings = get_settings()
    print(f"Database driver: {settings.db_driver}")

    if settings.db_driver == "sqlite":
        print("SQLite uses create_all only — no migration needed.")
        init_db()
        return 0

    print("Running schema migrations...")
    init_db()
    run_migrations(engine)
    print("Schema migration complete.")
    print("Restart the app and try registration again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
