"""Parser for Dahua ``multipart/x-mixed-replace`` event streams."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamPart:
    content_type: str
    body: bytes


class MixedReplaceParser:
    """Incremental parser for Dahua snapManager multipart bodies."""

    def __init__(self) -> None:
        self._boundary: bytes | None = None
        self._buffer = bytearray()
        self._pending_header = b""
        self._content_length: int | None = None
        self._content_type = ""
        self._reading_body = False

    def set_boundary_from_header(self, content_type: str) -> None:
        lowered = content_type.lower()
        if "boundary=" not in lowered:
            raise ValueError(f"Missing multipart boundary in Content-Type: {content_type}")
        boundary = content_type.split("boundary=", 1)[1].strip()
        if boundary.startswith('"') and boundary.endswith('"'):
            boundary = boundary[1:-1]
        self._boundary = boundary.encode("ascii")

    @property
    def boundary(self) -> bytes | None:
        return self._boundary

    def feed(self, chunk: bytes) -> list[StreamPart]:
        if not chunk:
            return []
        self._buffer.extend(chunk)
        parts: list[StreamPart] = []
        while True:
            if not self._reading_body:
                part = self._try_read_headers()
                if part is None:
                    break
                if part is False:
                    continue
            emitted = self._try_read_body()
            if emitted is None:
                break
            parts.append(emitted)
        return parts

    def _try_read_headers(self) -> StreamPart | None | bool:
        if self._boundary is None:
            return None

        data = bytes(self._buffer)
        marker = b"--" + self._boundary
        start = data.find(marker)
        if start == -1:
            if len(data) > len(marker) + 8:
                del self._buffer[: len(data) - len(marker)]
            return None

        after = start + len(marker)
        if data[after : after + 2] == b"--":
            del self._buffer[: after + 2]
            return False
        if data[after : after + 2] == b"\r\n":
            after += 2
        elif data[after : after + 1] == b"\n":
            after += 1
        else:
            return None

        header_end = data.find(b"\r\n\r\n", after)
        if header_end == -1:
            return None

        header_block = data[after:header_end].decode("utf-8", errors="replace")
        del self._buffer[: header_end + 4]

        self._content_length = None
        self._content_type = "application/octet-stream"
        for line in header_block.splitlines():
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            name = name.strip().lower()
            value = value.strip()
            if name == "content-length":
                try:
                    self._content_length = int(value)
                except ValueError:
                    self._content_length = None
            elif name == "content-type":
                self._content_type = value.split(";", 1)[0].strip().lower()

        if self._content_length is None:
            return False

        self._reading_body = True
        return False

    def _try_read_body(self) -> StreamPart | None:
        if self._content_length is None:
            return None
        if len(self._buffer) < self._content_length:
            return None

        body = bytes(self._buffer[: self._content_length])
        del self._buffer[: self._content_length]

        # Trailing CRLF before next boundary
        if len(self._buffer) >= 2 and self._buffer[:2] == b"\r\n":
            del self._buffer[:2]
        elif len(self._buffer) >= 1 and self._buffer[:1] == b"\n":
            del self._buffer[:1]

        part = StreamPart(content_type=self._content_type, body=body)
        self._reading_body = False
        self._content_length = None
        self._content_type = ""
        return part
