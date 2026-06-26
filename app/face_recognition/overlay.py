"""Face detection overlay — colored boxes like standard face-detection UIs."""

from __future__ import annotations

import cv2
import numpy as np

COLOR_RECOGNIZED = (0, 255, 0)
COLOR_UNKNOWN = (0, 0, 255)
COLOR_DETECTING = (0, 255, 255)


def _status_color(status: str) -> tuple[int, int, int]:
    if status == "Recognized":
        return COLOR_RECOGNIZED
    if status == "Unknown":
        return COLOR_UNKNOWN
    return COLOR_DETECTING


def draw_face_box(
    frame: np.ndarray,
    bbox: tuple[int, int, int, int],
    label: str,
    status: str,
    confidence: float | None = None,
) -> None:
    x, y, w, h = bbox
    color = _status_color(status)
    thickness = 3
    corner_len = max(12, min(w, h) // 4)

    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1)

    for cx, cy, dx, dy in (
        (x, y, corner_len, corner_len),
        (x + w, y, -corner_len, corner_len),
        (x, y + h, corner_len, -corner_len),
        (x + w, y + h, -corner_len, -corner_len),
    ):
        cv2.line(frame, (cx, cy), (cx + dx, cy), color, thickness)
        cv2.line(frame, (cx, cy), (cx, cy + dy), color, thickness)

    if confidence is not None:
        text = f"{label} {int(round(confidence * 100))}%"
    else:
        text = label

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    text_thickness = 2
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, text_thickness)
    label_y = max(y - 8, text_h + 8)
    cv2.rectangle(
        frame,
        (x, label_y - text_h - 6),
        (x + text_w + 8, label_y + baseline),
        color,
        -1,
    )
    cv2.putText(
        frame,
        text,
        (x + 4, label_y),
        font,
        font_scale,
        (255, 255, 255),
        text_thickness,
        cv2.LINE_AA,
    )


def draw_face_boxes(
    frame: np.ndarray,
    matches: list,
) -> np.ndarray:
    annotated = frame
    for match in matches:
        label = match.name if match.status == "Recognized" else "Unknown"
        draw_face_box(
            annotated,
            match.bbox,
            label,
            match.status,
            match.confidence,
        )
    return annotated
