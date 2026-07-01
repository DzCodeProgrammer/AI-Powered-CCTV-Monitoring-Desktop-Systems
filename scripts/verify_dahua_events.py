"""Verify Dahua event multipart parser and config (Phase 2)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.integrations.dahua.metadata import metadata_index_in_group, parse_event_metadata
from app.integrations.dahua.multipart import MixedReplaceParser


meta_body = b"Events[0].Code=FaceDetection\r\nIndexInGroup=1\r\n"
jpeg_body = b"\xff\xd8\xff\xd9"

SAMPLE = (
    b"--myboundary\r\n"
    b"Content-Type: text/plain\r\n"
    + f"Content-Length: {len(meta_body)}\r\n\r\n".encode()
    + meta_body
    + b"--myboundary\r\n"
    b"Content-Type: image/jpeg\r\n"
    + f"Content-Length: {len(jpeg_body)}\r\n\r\n".encode()
    + jpeg_body
    + b"--myboundary--\r\n"
)


def test_parser() -> None:
    parser = MixedReplaceParser()
    parser.set_boundary_from_header("multipart/x-mixed-replace; boundary=myboundary")
    parts = []
    for chunk in (SAMPLE[:80], SAMPLE[80:160], SAMPLE[160:]):
        parts.extend(parser.feed(chunk))
    assert len(parts) == 2, f"expected 2 parts, got {len(parts)}"
    assert parts[0].content_type == "text/plain"
    assert parts[1].content_type == "image/jpeg"
    assert parts[1].body == jpeg_body
    meta = parse_event_metadata(parts[0].body.decode())
    assert meta["Events[0].Code"] == "FaceDetection"
    assert metadata_index_in_group(meta) == 1
    print("OK: multipart parser")


def test_config() -> None:
    from app.utils.config import Settings

    s = Settings(
        dahua_host="192.168.1.10",
        cctv_mode="hybrid",
        dahua_event_enabled=True,
    )
    assert s.event_capture_active is True
    assert s.stream_monitor_active is True
    assert s.dahua_event_channel_resolved == s.dahua_channel

    s2 = Settings(cctv_mode="stream", dahua_event_enabled=True, dahua_host="x")
    assert s2.event_capture_active is False
    print("OK: event config flags")


def main() -> int:
    test_parser()
    test_config()
    print("verify_dahua_events: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
