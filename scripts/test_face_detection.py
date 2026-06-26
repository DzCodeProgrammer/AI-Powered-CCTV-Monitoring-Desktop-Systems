"""Quick test: webcam face detection (no server required)."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    import cv2

    from app.face_recognition.detector import FaceDetector
    from app.face_recognition.overlay import draw_face_boxes
    from app.face_recognition.recognizer import FaceMatch, STATUS_DETECTING
    from app.utils.config import get_settings

    settings = get_settings()
    detector = FaceDetector(settings)
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    if sys.platform == "win32":
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print(f"FAIL: cannot open webcam index {index}")
        return 1

    print(f"Webcam {index} opened. Press Q to quit.")
    print(f"Detector: {settings.face_detector} | low_light={settings.detection_low_light}")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("FAIL: no frame from webcam")
            break

        boxes = detector.detect(frame)
        display = frame.copy()
        matches = [
            FaceMatch("Detecting", STATUS_DETECTING, 0.0, None, box) for box in boxes
        ]
        draw_face_boxes(display, matches)
        cv2.putText(
            display,
            f"Faces: {len(boxes)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        cv2.imshow("Face detection test", display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
