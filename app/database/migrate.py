from __future__ import annotations

"""Apply lightweight schema migrations for databases created in early sessions."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def _table_columns(engine: Engine, table: str) -> set[str]:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def _rename_column(
    engine: Engine,
    table: str,
    old: str,
    new: str,
    column_type: str,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(f"ALTER TABLE `{table}` CHANGE COLUMN `{old}` `{new}` {column_type}")
        )
    logger.info("Renamed %s.%s -> %s", table, old, new)


def _add_column(engine: Engine, table: str, column: str, definition: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"))
    logger.info("Added column %s.%s", table, column)


def migrate_users(engine: Engine) -> None:
    cols = _table_columns(engine, "users")
    if not cols:
        return

    if "name" in cols and "full_name" not in cols:
        _rename_column(engine, "users", "name", "full_name", "VARCHAR(100) NOT NULL")

    cols = _table_columns(engine, "users")
    if "registered_at" in cols and "created_at" not in cols:
        _rename_column(engine, "users", "registered_at", "created_at", "DATETIME NULL")

    cols = _table_columns(engine, "users")
    if "embedding_path" not in cols:
        _add_column(engine, "users", "embedding_path", "VARCHAR(500) NULL")

    cols = _table_columns(engine, "users")
    if "is_active" not in cols:
        _add_column(engine, "users", "is_active", "TINYINT(1) NOT NULL DEFAULT 1")


def migrate_attendance(engine: Engine) -> None:
    tables = inspect(engine).get_table_names()
    if "attendance" in tables and "attendance_logs" not in tables:
        with engine.begin() as conn:
            conn.execute(text("RENAME TABLE `attendance` TO `attendance_logs`"))
        logger.info("Renamed table attendance -> attendance_logs")

    cols = _table_columns(engine, "attendance_logs")
    if not cols:
        return

    if "person_name" in cols and "detected_name" not in cols:
        _rename_column(
            engine,
            "attendance_logs",
            "person_name",
            "detected_name",
            "VARCHAR(100) NOT NULL",
        )

    cols = _table_columns(engine, "attendance_logs")
    if "detection_time" in cols and "detected_at" not in cols:
        _rename_column(
            engine,
            "attendance_logs",
            "detection_time",
            "detected_at",
            "DATETIME NULL",
        )


def migrate_unknown_faces(engine: Engine) -> None:
    cols = _table_columns(engine, "unknown_faces")
    if not cols:
        return

    if "screenshot_path" in cols and "image_path" not in cols:
        _rename_column(
            engine,
            "unknown_faces",
            "screenshot_path",
            "image_path",
            "VARCHAR(500) NOT NULL",
        )

    cols = _table_columns(engine, "unknown_faces")
    if "camera_source" not in cols:
        _add_column(engine, "unknown_faces", "camera_source", "VARCHAR(200) NULL")

    cols = _table_columns(engine, "unknown_faces")
    if "notes" not in cols:
        _add_column(engine, "unknown_faces", "notes", "VARCHAR(500) NULL")


def run_migrations(engine: Engine) -> None:
    if engine.dialect.name == "sqlite":
        return

    try:
        migrate_users(engine)
        migrate_attendance(engine)
        migrate_unknown_faces(engine)
    except Exception as exc:
        logger.error("Schema migration failed: %s", exc)
        raise
