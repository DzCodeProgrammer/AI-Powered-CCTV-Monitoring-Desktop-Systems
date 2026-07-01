"""Convert OpenCV BGR frames to Qt images."""

from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap


def bgr_to_qpixmap(frame: np.ndarray, max_display_width: int = 0) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb = np.ascontiguousarray(rgb)
    height, width, channels = rgb.shape
    image = QImage(
        rgb.data,
        width,
        height,
        channels * width,
        QImage.Format.Format_RGB888,
    )
    pixmap = QPixmap.fromImage(image.copy())
    if max_display_width > 0 and pixmap.width() > max_display_width:
        pixmap = pixmap.scaledToWidth(
            max_display_width,
            Qt.TransformationMode.SmoothTransformation,
        )
    return pixmap


def fit_pixmap_to_label(pixmap: QPixmap, label_size: QSize) -> QPixmap:
    return pixmap.scaled(
        label_size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
