"""Subscribe to Dahua IPC FaceDetection events via snapManager.cgi."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx

from app.integrations.dahua.metadata import (
    metadata_event_code,
    metadata_index_in_group,
    parse_event_metadata,
)
from app.integrations.dahua.multipart import MixedReplaceParser, StreamPart
from app.utils.config import Settings
from app.utils.logging import get_logger

logger = get_logger("dahua.events")

EventHandler = Callable[[bytes, dict[str, str]], Awaitable[None]]
LifecycleHook = Callable[[], Awaitable[None]]


class DahuaEventSubscriber:
    """Long-lived HTTP subscriber for Dahua FaceDetection multipart stream."""

    def __init__(
        self,
        settings: Settings,
        on_snapshot: EventHandler,
        on_connected: LifecycleHook | None = None,
    ) -> None:
        self.settings = settings
        self.on_snapshot = on_snapshot
        self.on_connected = on_connected
        self._stop = asyncio.Event()

    def request_stop(self) -> None:
        self._stop.set()

    def _attach_url(self) -> str:
        channel = self.settings.dahua_event_channel_resolved
        heartbeat = self.settings.dahua_event_heartbeat
        host = self.settings.dahua_host
        port = self.settings.dahua_http_port
        return (
            f"http://{host}:{port}/cgi-bin/snapManager.cgi"
            f"?action=attachFileProc&channel={channel}&heartbeat={heartbeat}"
            f"&Flags[0]=Event&Events=[FaceDetection,EventBaseInfo]"
        )

    async def run(self) -> None:
        if not self.settings.dahua_host:
            logger.warning("Dahua event subscriber skipped: DAHUA_HOST not set")
            return

        url = self._attach_url()
        timeout = httpx.Timeout(
            None,
            connect=self.settings.dahua_event_timeout,
            read=self.settings.dahua_event_timeout,
        )
        auth = httpx.DigestAuth(self.settings.dahua_username, self.settings.dahua_password)

        logger.info(
            "Connecting Dahua event stream host=%s port=%s channel=%s",
            self.settings.dahua_host,
            self.settings.dahua_http_port,
            self.settings.dahua_event_channel_resolved,
        )

        async with httpx.AsyncClient(auth=auth, timeout=timeout) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                if self.on_connected:
                    await self.on_connected()
                content_type = response.headers.get("content-type", "")
                parser = MixedReplaceParser()
                parser.set_boundary_from_header(content_type)
                pending_meta: dict[str, str] = {}

                async for chunk in response.aiter_bytes():
                    if self._stop.is_set():
                        break
                    for part in parser.feed(chunk):
                        await self._handle_part(part, pending_meta)

    async def _handle_part(
        self,
        part: StreamPart,
        pending_meta: dict[str, str],
    ) -> None:
        if part.content_type.startswith("text/"):
            pending_meta.clear()
            pending_meta.update(parse_event_metadata(part.body.decode("utf-8", errors="replace")))
            return

        if not part.content_type.startswith("image/"):
            return

        index = metadata_index_in_group(pending_meta)
        if index != 1:
            logger.debug("Skipping face crop snapshot IndexInGroup=%s", index)
            pending_meta.clear()
            return

        code = metadata_event_code(pending_meta)
        if code and code.lower() not in {"facedetection", "face detection"}:
            logger.debug("Ignoring event code=%s", code)
            pending_meta.clear()
            return

        meta = dict(pending_meta)
        pending_meta.clear()
        try:
            await self.on_snapshot(part.body, meta)
        except Exception as exc:
            logger.warning("Event snapshot handler failed: %s", exc)


async def run_subscriber_with_reconnect(
    settings: Settings,
    on_snapshot: EventHandler,
    stop_event: asyncio.Event,
    on_connected: LifecycleHook | None = None,
    on_disconnected: LifecycleHook | None = None,
) -> None:
    """Reconnect loop with configurable delay (Dahua.docx: ~5s)."""
    delay = settings.dahua_event_reconnect
    while not stop_event.is_set():
        subscriber = DahuaEventSubscriber(settings, on_snapshot, on_connected=on_connected)
        try:
            from app.utils.config import get_settings

            get_settings.cache_clear()
            subscriber.settings = get_settings()
            await subscriber.run()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Dahua event stream disconnected: %s", exc)
        finally:
            if on_disconnected:
                await on_disconnected()
        if stop_event.is_set():
            break
        logger.info("Reconnecting Dahua event stream in %.0fs", delay)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=delay)
        except asyncio.TimeoutError:
            pass
