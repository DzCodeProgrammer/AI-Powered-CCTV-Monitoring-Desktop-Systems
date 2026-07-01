"""Parse Dahua snapManager event metadata (text/plain key=value)."""

from __future__ import annotations


def parse_event_metadata(text: str) -> dict[str, str]:
    """Flatten Dahua event lines like ``Events[0].Code=FaceDetection``."""
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def metadata_index_in_group(meta: dict[str, str]) -> int:
    for key in ("IndexInGroup", "Events[0].IndexInGroup"):
        if key in meta:
            try:
                return int(meta[key])
            except ValueError:
                return 1
    return 1


def metadata_event_code(meta: dict[str, str]) -> str:
    return meta.get("Events[0].Code") or meta.get("Code") or ""
