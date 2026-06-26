from __future__ import annotations

import time
from dataclasses import dataclass, field

import cv2
import numpy as np
from deepface import DeepFace

from app.face_recognition.detector import FaceDetector
from app.face_recognition.embeddings import (
    EmbeddingStore,
    cosine_distance,
    parse_embedding,
)
from app.face_recognition.frame_utils import crop_face, resize_frame, scale_bbox
from app.face_recognition.overlay import draw_face_boxes
from app.utils.config import Settings
from app.utils.logging import log_exception

STATUS_RECOGNIZED = "Recognized"
STATUS_UNKNOWN = "Unknown"
STATUS_DETECTING = "Detecting"


@dataclass
class FaceMatch:
    name: str
    status: str
    confidence: float
    user_id: int | None
    bbox: tuple[int, int, int, int]


@dataclass
class _FaceTrack:
    bbox: tuple[int, int, int, int]
    name: str = "Detecting"
    status: str = STATUS_DETECTING
    confidence: float = 0.0
    user_id: int | None = None
    last_recognition: float = field(default_factory=lambda: 0.0)


class FaceRecognizer:
    FACE_EMBED_MAX_SIZE = 160

    def __init__(self, settings: Settings, embedding_store: EmbeddingStore) -> None:
        self.settings = settings
        self.embedding_store = embedding_store
        self.detector = FaceDetector(settings)
        self._frame_index = 0
        self._tracks: list[_FaceTrack] = []
        self._last_matches: list[FaceMatch] = []
        self._perf = settings.performance_profile

    def update_embeddings(self, embedding_store: EmbeddingStore) -> None:
        self.embedding_store = embedding_store

    def reset_tracking(self) -> None:
        """Clear tracks when camera source changes."""
        self._frame_index = 0
        self._tracks = []
        self._last_matches = []

    @property
    def deepface_call_count(self) -> int:
        return getattr(self, "_deepface_calls", 0)

    def _match_face(self, face_image: np.ndarray) -> tuple[str, str, float, int | None]:
        if self.embedding_store.is_empty() or face_image.size == 0:
            return "Unknown", STATUS_UNKNOWN, 0.0, None

        try:
            rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            height, width = rgb.shape[:2]
            if max(height, width) > self.FACE_EMBED_MAX_SIZE:
                scale = self.FACE_EMBED_MAX_SIZE / max(height, width)
                rgb = cv2.resize(
                    rgb,
                    (int(width * scale), int(height * scale)),
                    interpolation=cv2.INTER_AREA,
                )

            self._deepface_calls = getattr(self, "_deepface_calls", 0) + 1
            vector = DeepFace.represent(
                img_path=rgb,
                model_name=self.settings.face_model,
                enforce_detection=False,
                detector_backend="skip",
            )
            face_embedding = parse_embedding(vector)
        except Exception as exc:
            log_exception("face_recognition", "Face embedding failed during match", exc)
            return "Unknown", STATUS_UNKNOWN, 0.0, None

        distances = [
            cosine_distance(face_embedding, entry.embedding)
            for entry in self.embedding_store.entries
        ]
        ranked = sorted(enumerate(distances), key=lambda item: item[1])
        best_index, best_distance = ranked[0]
        best_distance = float(best_distance)
        best_entry = self.embedding_store.entries[best_index]

        if len(ranked) >= 2:
            second_best = float(ranked[1][1])
            margin = second_best - best_distance
            if margin < self.settings.recognition_margin:
                return "Unknown", STATUS_UNKNOWN, max(0.0, 1.0 - best_distance), None

        if best_distance < self.settings.recognition_threshold:
            confidence = max(0.0, 1.0 - best_distance)
            return best_entry.name, STATUS_RECOGNIZED, confidence, best_entry.user_id

        return "Unknown", STATUS_UNKNOWN, max(0.0, 1.0 - best_distance), None

    def _bbox_center(self, bbox: tuple[int, int, int, int]) -> tuple[float, float]:
        x, y, w, h = bbox
        return x + w / 2, y + h / 2

    def _bbox_distance(
        self,
        a: tuple[int, int, int, int],
        b: tuple[int, int, int, int],
    ) -> float:
        ax, ay = self._bbox_center(a)
        bx, by = self._bbox_center(b)
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    def _update_tracks(self, bboxes: list[tuple[int, int, int, int]]) -> None:
        max_faces = int(self._perf["max_faces_per_frame"])
        bboxes = bboxes[:max_faces]
        used: set[int] = set()
        new_tracks: list[_FaceTrack] = []

        for bbox in bboxes:
            best_idx = None
            best_dist = float("inf")
            for idx, track in enumerate(self._tracks):
                if idx in used:
                    continue
                dist = self._bbox_distance(bbox, track.bbox)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = idx

            if best_idx is not None and best_dist < 80:
                used.add(best_idx)
                old = self._tracks[best_idx]
                new_tracks.append(
                    _FaceTrack(
                        bbox=bbox,
                        name=old.name,
                        status=old.status,
                        confidence=old.confidence,
                        user_id=old.user_id,
                        last_recognition=old.last_recognition,
                    )
                )
            else:
                new_tracks.append(_FaceTrack(bbox=bbox))

        self._tracks = new_tracks

    def _run_recognition(self, frame: np.ndarray) -> None:
        now = time.time()
        interval = float(self._perf["recognition_interval"])

        for track in self._tracks:
            if now - track.last_recognition < interval:
                continue
            face_roi = crop_face(frame, track.bbox)
            name, status, confidence, user_id = self._match_face(face_roi)
            track.name = name
            track.status = status
            track.confidence = confidence
            track.user_id = user_id
            track.last_recognition = now

    def _tracks_to_matches(self) -> list[FaceMatch]:
        return [
            FaceMatch(
                name=track.name,
                status=track.status,
                confidence=track.confidence,
                user_id=track.user_id,
                bbox=track.bbox,
            )
            for track in self._tracks
        ]

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, list[FaceMatch]]:
        perf = self._perf
        frame_skip = int(perf["frame_skip"])
        should_process = self._frame_index % frame_skip == 0
        self._frame_index += 1

        display, display_scale = resize_frame(frame, int(perf["stream_max_width"]))

        if not should_process:
            matches = self._last_matches
            annotated = draw_face_boxes(display, matches)
            return annotated, matches

        if should_process:
            detect_every = frame_skip * int(perf["detection_frame_skip"])
            if not self._tracks or (self._frame_index - 1) % detect_every == 0:
                proc_frame, proc_scale = resize_frame(frame, int(perf["process_max_width"]))
                bboxes = self.detector.detect(proc_frame)
                full_bboxes = [scale_bbox(b, proc_scale) for b in bboxes]
                display_bboxes = [scale_bbox(b, 1 / display_scale) for b in full_bboxes]
                self._update_tracks(display_bboxes)

        if self._tracks:
            self._run_recognition(display)

        matches = self._tracks_to_matches()
        self._last_matches = matches
        annotated = draw_face_boxes(display, matches)

        if not matches:
            cv2.putText(
                annotated,
                "No face detected - face the camera, improve lighting",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

        return annotated, matches
