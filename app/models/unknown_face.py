from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, synonym

from app.database.base import Base


class UnknownFace(Base):
    __tablename__ = "unknown_faces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    camera_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    screenshot_path = synonym("image_path")
