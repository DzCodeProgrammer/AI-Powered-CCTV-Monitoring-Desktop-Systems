from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    embedding_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
