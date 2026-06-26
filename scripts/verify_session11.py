"""Verify Session 11: performance pipeline and face box overlay."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    from app.face_recognition.embeddings import EmbeddingStore
    from app.face_recognition.frame_utils import resize_frame, scale_bbox
    from app.face_recognition.overlay import COLOR_RECOGNIZED, COLOR_UNKNOWN, draw_face_box
    from app.face_recognition.recognizer import FaceMatch, FaceRecognizer, STATUS_RECOGNIZED
    from app.utils.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    perf = settings.performance_profile

    if not perf.get("low_end_mode"):
        print("WARN: LOW_END_MODE is off (defaults expect low-end tuning)")
    if int(perf["process_max_width"]) > 640:
        print("FAIL: process_max_width should be <= 640 in low-end mode")
        return 1
    print(f"Performance profile: frame_skip={perf['frame_skip']}, "
          f"recognition_interval={perf['recognition_interval']}s")

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    resized, scale = resize_frame(frame, 640)
    if resized.shape[1] != 640:
        print("FAIL: resize_frame should downscale to 640 width")
        return 1
    bbox = scale_bbox((10, 10, 50, 50), scale)
    if bbox[2] <= 50:
        print("FAIL: scale_bbox should expand width when scaling up")
        return 1
    print("Frame resize + bbox scale: OK")

    draw_face_box(frame, (100, 100, 120, 120), "Test User", STATUS_RECOGNIZED, 0.92)
    if not np.any(frame[100:220, 100:220] == COLOR_RECOGNIZED):
        print("FAIL: face box should draw green pixels on frame")
        return 1
    print("Colored face detection boxes: OK")

    store = EmbeddingStore(entries=[])
    recognizer = FaceRecognizer(settings, store)

    with patch.object(recognizer.detector, "detect", return_value=[(20, 20, 80, 80)]):
        with patch.object(
            recognizer,
            "_match_face",
            return_value=("Alice", STATUS_RECOGNIZED, 0.88, 1),
        ) as mock_match:
            _, matches = recognizer.process_frame(frame)
            calls_after_first = mock_match.call_count

            for _ in range(int(perf["frame_skip"]) - 1):
                recognizer.process_frame(frame)

            calls_after_skips = mock_match.call_count
            if calls_after_skips != calls_after_first:
                print("FAIL: DeepFace should not run on skipped frames")
                return 1

            for _ in range(5):
                recognizer.process_frame(frame)

            if mock_match.call_count > calls_after_first + 2:
                print("FAIL: DeepFace called too frequently (not throttled)")
                return 1

    if not matches:
        print("FAIL: expected at least one face match")
        return 1
    if matches[0].status != STATUS_RECOGNIZED:
        print("FAIL: expected recognized status on match")
        return 1
    print("Frame skip + DeepFace throttle: OK")

    yellow = (0, 255, 255)
    draw_face_box(frame, (300, 100, 100, 100), "Detecting", "Detecting", None)
    if not np.any(frame == yellow):
        print("FAIL: detecting state should use yellow box")
        return 1
    print("Detecting (yellow) box: OK")

    print("Session 11 performance verification: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
