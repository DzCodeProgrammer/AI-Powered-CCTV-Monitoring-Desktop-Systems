from __future__ import annotations

import cv2
import numpy as np

from app.utils.config import Settings


class FaceDetector:
    def __init__(self, settings: Settings | None = None) -> None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(cascade_path)
        if self._cascade.empty():
            raise RuntimeError("Failed to load Haar cascade classifier.")
        self._min_size = settings.face_min_size if settings else 48

    def detect(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.12,
            minNeighbors=5,
            minSize=(self._min_size, self._min_size),
        )
        return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]
