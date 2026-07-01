"""Register new persons from the desktop app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.recognition_service import rebuild_embeddings
from app.services.registration_service import (
    MAX_EXTRA_IMAGES,
    RegistrationError,
    register_person_with_extras,
)
from app.utils.config import get_settings


@dataclass
class _UploadShim:
    filename: str


class RegisterPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        header = QLabel("Register New Person")
        header.setStyleSheet("font-size: 15px; font-weight: 600;")

        hint = QLabel(
            "Upload a clear face photo. Add extra training photos for better accuracy."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 12px;")

        self._name = QLineEdit()
        self._name.setPlaceholderText("Full name (unique)")

        self._phone = QLineEdit()
        self._phone.setPlaceholderText("628… or 08… (optional)")

        self._primary_label = QLabel("No primary photo selected")
        self._primary_label.setStyleSheet("color: #444;")

        self._extra_label = QLabel("No extra photos selected")
        self._extra_label.setStyleSheet("color: #444;")

        primary_btn = QPushButton("Choose primary photo…")
        primary_btn.clicked.connect(self._pick_primary)

        extra_btn = QPushButton("Choose extra photos…")
        extra_btn.clicked.connect(self._pick_extras)

        self._submit = QPushButton("Register person")
        self._submit.clicked.connect(self._register)

        form = QFormLayout()
        form.addRow("Full name", self._name)
        form.addRow("WhatsApp", self._phone)
        form.addRow("Primary photo", self._primary_label)
        form.addRow("", primary_btn)
        form.addRow("Extra photos", self._extra_label)
        form.addRow("", extra_btn)

        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(self._submit)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addStretch()

        self._primary_path: Path | None = None
        self._extra_paths: list[Path] = []

    def _pick_primary(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Primary face photo",
            "",
            "Images (*.jpg *.jpeg *.png *.webp)",
        )
        if not path:
            return
        self._primary_path = Path(path)
        self._primary_label.setText(self._primary_path.name)

    def _pick_extras(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Extra training photos",
            "",
            "Images (*.jpg *.jpeg *.png *.webp)",
        )
        if not paths:
            return
        self._extra_paths = [Path(path) for path in paths[:MAX_EXTRA_IMAGES]]
        self._extra_label.setText(f"{len(self._extra_paths)} photo(s) selected")

    def _register(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Register", "Full name is required.")
            return
        if self._primary_path is None or not self._primary_path.is_file():
            QMessageBox.warning(self, "Register", "Choose a primary face photo.")
            return

        settings = get_settings()
        primary_content = self._primary_path.read_bytes()
        primary_file = _UploadShim(self._primary_path.name)

        extras: list[tuple[_UploadShim, bytes]] = []
        for path in self._extra_paths:
            extras.append((_UploadShim(path.name), path.read_bytes()))

        db = SessionLocal()
        try:
            user = register_person_with_extras(
                db,
                settings,
                name,
                primary_file,  # type: ignore[arg-type]
                primary_content,
                extras,  # type: ignore[arg-type]
                phone_number=self._phone.text().strip() or None,
            )
            store = rebuild_embeddings(db, settings)
            count = len(store.entries)
        except RegistrationError as exc:
            QMessageBox.warning(self, "Register", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Register", f"Registration failed:\n{exc}")
            return
        finally:
            db.close()

        QMessageBox.information(
            self,
            "Register",
            f"Registered {user.full_name}.\nEmbeddings rebuilt for {count} person(s).",
        )
        self._name.clear()
        self._phone.clear()
        self._primary_path = None
        self._extra_paths = []
        self._primary_label.setText("No primary photo selected")
        self._extra_label.setText("No extra photos selected")
