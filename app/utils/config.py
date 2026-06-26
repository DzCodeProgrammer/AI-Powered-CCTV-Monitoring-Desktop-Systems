from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Smart CCTV Face Recognition"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "dev-secret"

    host: str = "127.0.0.1"
    port: int = 8000

    db_driver: Literal["sqlite", "mysql"] = "sqlite"
    database_url: str | None = None

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "smart_cctv"

    camera_source: str = "0"
    rtsp_url: str = ""

    dahua_username: str = ""
    dahua_password: str = ""
    dahua_host: str = ""
    dahua_port: int = 554
    dahua_channel: int = 1
    dahua_subtype: int = 0

    face_model: str = "Facenet512"
    recognition_threshold: float = 0.45
    recognition_margin: float = 0.08
    detection_interval: float = 30.0
    attendance_interval: float = 300.0

    # Performance (Session 11) — tuned for i5 Gen4 / 8GB RAM
    low_end_mode: bool = True
    frame_skip: int = 2
    detection_frame_skip: int = 2
    recognition_interval: float = 30.0
    process_max_width: int = 640
    stream_max_width: int = 960
    jpeg_quality: int = 72
    max_faces_per_frame: int = 2
    face_min_size: int = 36
    detection_low_light: bool = True
    face_detector: Literal["auto", "yunet", "haar"] = "auto"
    yunet_score_threshold: float = 0.45

    dataset_dir: str = "datasets"
    screenshot_dir: str = "screenshots"
    log_dir: str = "logs"

    session_max_age: int = 86400
    admin_username: str = "admin"
    admin_password: str = ""

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_driver == "mysql":
            user = quote_plus(self.db_user)
            password = quote_plus(self.db_password)
            return (
                f"mysql+pymysql://{user}:{password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
                f"?charset=utf8mb4"
            )
        return f"sqlite:///{Path('database/smart_cctv.db').resolve()}"

    @property
    def dahua_rtsp_url(self) -> str:
        if not self.dahua_host:
            raise ValueError("DAHUA_HOST is required when CAMERA_SOURCE=dahua")
        user = quote_plus(self.dahua_username)
        password = quote_plus(self.dahua_password)
        return (
            f"rtsp://{user}:{password}@{self.dahua_host}:{self.dahua_port}"
            f"/cam/realmonitor?channel={self.dahua_channel}&subtype={self.dahua_subtype}"
        )

    @property
    def resolved_camera_source(self) -> str:
        source = self.camera_source.strip()
        lowered = source.lower()
        if lowered in {"dahua", "ip", "cctv"}:
            if self.rtsp_url:
                return self.rtsp_url
            return self.dahua_rtsp_url
        if lowered.startswith("rtsp://"):
            return source
        return source

    @property
    def camera_mode_label(self) -> str:
        source = self.camera_source.strip().lower()
        if source in {"dahua", "ip", "cctv"}:
            return "dahua"
        if source.startswith("rtsp://"):
            return "rtsp"
        return "webcam"

    @property
    def performance_profile(self) -> dict[str, int | float | bool]:
        if self.low_end_mode:
            return {
                "low_end_mode": True,
                "frame_skip": max(self.frame_skip, 2),
                "detection_frame_skip": max(self.detection_frame_skip, 2),
                "recognition_interval": max(self.recognition_interval, 2.0),
                "process_max_width": min(self.process_max_width, 640),
                "stream_max_width": min(self.stream_max_width, 960),
                "jpeg_quality": min(self.jpeg_quality, 75),
                "max_faces_per_frame": min(self.max_faces_per_frame, 2),
            }
        return {
            "low_end_mode": False,
            "frame_skip": self.frame_skip,
            "detection_frame_skip": self.detection_frame_skip,
            "recognition_interval": self.recognition_interval,
            "process_max_width": self.process_max_width,
            "stream_max_width": self.stream_max_width,
            "jpeg_quality": self.jpeg_quality,
            "max_faces_per_frame": self.max_faces_per_frame,
        }

    @property
    def safe_camera_display(self) -> str:
        return mask_sensitive_url(self.resolved_camera_source)


def mask_sensitive_url(source: str) -> str:
    if not source.lower().startswith("rtsp://"):
        return source
    parsed = urlparse(source)
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"***:***@{host}{port}"
    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
