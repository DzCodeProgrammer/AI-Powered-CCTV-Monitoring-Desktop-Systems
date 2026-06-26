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

    face_model: str = "Facenet"
    recognition_threshold: float = 0.55
    detection_interval: float = 1.0
    attendance_interval: float = 300.0

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
