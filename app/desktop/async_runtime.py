"""Background asyncio loop for Dahua events and maintenance (desktop mode)."""

from __future__ import annotations

import asyncio
import threading

from app.services.background_tasks import maintenance_loop
from app.services.dahua_event_service import start_event_capture, stop_event_capture
from app.utils.logging import get_logger

logger = get_logger("desktop.async")

_loop: asyncio.AbstractEventLoop | None = None
_thread: threading.Thread | None = None
_maintenance_task: asyncio.Task | None = None


def _run_loop() -> None:
    global _loop, _maintenance_task
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)

    async def _startup() -> None:
        global _maintenance_task
        await start_event_capture()
        _maintenance_task = asyncio.create_task(maintenance_loop(), name="desktop-maintenance")

    async def _shutdown() -> None:
        global _maintenance_task
        await stop_event_capture()
        if _maintenance_task is not None:
            _maintenance_task.cancel()
            try:
                await _maintenance_task
            except asyncio.CancelledError:
                pass
            _maintenance_task = None

    try:
        _loop.run_until_complete(_startup())
        _loop.run_forever()
    finally:
        try:
            _loop.run_until_complete(_shutdown())
        except Exception as exc:
            logger.warning("Desktop async shutdown: %s", exc)
        _loop.close()


def start_background_tasks() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_run_loop, name="desktop-async", daemon=True)
    _thread.start()
    logger.info("Desktop background tasks started")


def stop_background_tasks() -> None:
    global _loop, _thread
    if _loop is None or not _loop.is_running():
        return

    async def _shutdown() -> None:
        global _maintenance_task
        await stop_event_capture()
        if _maintenance_task is not None:
            _maintenance_task.cancel()
            try:
                await _maintenance_task
            except asyncio.CancelledError:
                pass
            _maintenance_task = None

    future = asyncio.run_coroutine_threadsafe(_shutdown(), _loop)
    try:
        future.result(timeout=5.0)
    except Exception as exc:
        logger.warning("Desktop async stop: %s", exc)
    _loop.call_soon_threadsafe(_loop.stop)
    if _thread is not None:
        _thread.join(timeout=3.0)
    _thread = None
    _loop = None
