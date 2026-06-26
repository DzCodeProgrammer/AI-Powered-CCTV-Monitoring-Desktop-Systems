"""Frame resize and bbox coordinate helpers for performance pipeline."""

from __future__ import annotations

import cv2
import numpy as np


def resize_frame(
    frame: np.ndarray,
    max_width: int,
) -> tuple[np.ndarray, float]:
    """Return resized frame and scale factor (original / resized)."""
    if max_width <= 0:
        return frame, 1.0

    height, width = frame.shape[:2]
    if width <= max_width:
        return frame, 1.0

    scale = max_width / width
    new_size = (max_width, int(height * scale))
    resized = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)
    return resized, width / max_width


def scale_bbox(
    bbox: tuple[int, int, int, int],
    scale: float,
) -> tuple[int, int, int, int]:
    x, y, w, h = bbox
    return (
        int(x * scale),
        int(y * scale),
        int(w * scale),
        int(h * scale),
    )


def crop_face(frame: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = bbox
    height, width = frame.shape[:2]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(width, x + w)
    y2 = min(height, y + h)
    if x2 <= x1 or y2 <= y1:
        return frame[0:0, 0:0]
    return frame[y1:y2, x1:x2]
