"""Remove old log and screenshot files to save disk space on HDD laptops."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from app.utils.config import Settings
from app.utils.logging import get_logger

logger = get_logger("cleanup")

_last_cleanup_at: float = 0.0


@dataclass
class CleanupResult:
    logs_removed: int
    screenshots_removed: int
    bytes_freed: int


def _remove_older_than(directory: Path, retention_days: int, suffixes: tuple[str, ...]) -> tuple[int, int]:
    if not directory.is_dir() or retention_days < 1:
        return 0, 0

    cutoff = time.time() - (retention_days * 86400)
    removed = 0
    freed = 0

    for path in directory.iterdir():
        if not path.is_file():
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        try:
            if path.stat().st_mtime >= cutoff:
                continue
            size = path.stat().st_size
            path.unlink(missing_ok=True)
            removed += 1
            freed += size
        except OSError as exc:
            logger.warning("Could not delete %s: %s", path, exc)

    return removed, freed


def run_cleanup(settings: Settings) -> CleanupResult:
    log_dir = Path(settings.log_dir)
    screenshot_dir = Path(settings.screenshot_dir)

    logs_removed, logs_freed = _remove_older_than(
        log_dir,
        settings.log_retention_days,
        (".log",),
    )
    shots_removed, shots_freed = _remove_older_than(
        screenshot_dir,
        settings.screenshot_retention_days,
        (".jpg", ".jpeg", ".png", ".webp"),
    )

    total_freed = logs_freed + shots_freed
    if logs_removed or shots_removed:
        logger.info(
            "Cleanup removed %s log(s) and %s screenshot(s), freed ~%.1f MB",
            logs_removed,
            shots_removed,
            total_freed / (1024 * 1024),
        )

    return CleanupResult(
        logs_removed=logs_removed,
        screenshots_removed=shots_removed,
        bytes_freed=total_freed,
    )


def maybe_run_cleanup(settings: Settings) -> CleanupResult | None:
    global _last_cleanup_at
    if not settings.cleanup_enabled:
        return None

    interval_seconds = max(1, settings.cleanup_interval_hours) * 3600
    now = time.time()
    if _last_cleanup_at and (now - _last_cleanup_at) < interval_seconds:
        return None

    result = run_cleanup(settings)
    _last_cleanup_at = now
    return result
