from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UnknownFace(Base):
    __tablename__ = "unknown_faces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    screenshot_path: Mapped[str] = mapped_column(String(500), nullable=False)
    camera_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
