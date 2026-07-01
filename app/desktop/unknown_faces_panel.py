"""Unknown face gallery for desktop."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.desktop.file_utils import resolve_stored_path
from app.models.unknown_face import UnknownFace
from app.services.recognition_service import rebuild_embeddings
from app.services.registration_service import RegistrationError, register_person_from_image_file
from app.services.unknown_face_service import (
    count_unknown_faces,
    delete_all_unknown_faces,
    delete_unknown_face,
)
from app.utils.config import get_settings
from app.utils.datetime_local import format_datetime_local
from sqlalchemy import select


class UnknownFacesPanel(QWidget):
    THUMB_SIZE = 72

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        header = QLabel("Unknown Faces")
        header.setStyleSheet("font-size: 15px; font-weight: 600;")

        self._summary = QLabel("Loading…")
        self._summary.setStyleSheet("color: #666; font-size: 12px;")

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Photo", "Detected", "Camera", "ID"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setColumnWidth(0, self.THUMB_SIZE + 16)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setDefaultSectionSize(self.THUMB_SIZE + 8)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_faces)

        register_btn = QPushButton("Register selected…")
        register_btn.clicked.connect(self._register_selected)

        delete_btn = QPushButton("Delete selected")
        delete_btn.clicked.connect(self._delete_selected)

        delete_all_btn = QPushButton("Delete all")
        delete_all_btn.clicked.connect(self._delete_all)

        actions = QHBoxLayout()
        actions.addWidget(refresh_btn)
        actions.addWidget(register_btn)
        actions.addWidget(delete_btn)
        actions.addStretch()
        actions.addWidget(delete_all_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(self._summary)
        layout.addWidget(self._table, stretch=1)
        layout.addLayout(actions)

        self.load_faces()

    def load_faces(self) -> None:
        db = SessionLocal()
        try:
            faces = list(
                db.scalars(
                    select(UnknownFace).order_by(UnknownFace.detected_at.desc()).limit(60)
                ).all()
            )
            total = count_unknown_faces(db)
        finally:
            db.close()

        self._summary.setText(f"{total} unknown face record(s) in database")
        self._table.setRowCount(len(faces))

        for row, face in enumerate(faces):
            thumb = QLabel()
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            file_path = resolve_stored_path(face.image_path)
            if file_path is not None:
                pixmap = QPixmap(str(file_path)).scaled(
                    self.THUMB_SIZE,
                    self.THUMB_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                thumb.setPixmap(pixmap)
            else:
                thumb.setText("missing")

            when = QTableWidgetItem(
                format_datetime_local(face.detected_at, include_zone=True)
            )
            camera = QTableWidgetItem(face.camera_source or "-")
            face_id = QTableWidgetItem(str(face.id))
            face_id.setData(Qt.ItemDataRole.UserRole, face.id)

            self._table.setCellWidget(row, 0, thumb)
            self._table.setItem(row, 1, when)
            self._table.setItem(row, 2, camera)
            self._table.setItem(row, 3, face_id)

    def _selected_face_id(self) -> int | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self._table.item(rows[0].row(), 3)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def _register_selected(self) -> None:
        face_id = self._selected_face_id()
        if face_id is None:
            QMessageBox.information(self, "Unknown faces", "Select a row first.")
            return

        name, ok = QInputDialog.getText(self, "Register person", "Full name:")
        if not ok or not name.strip():
            return

        phone, ok_phone = QInputDialog.getText(
            self,
            "Register person",
            "WhatsApp (optional):",
        )
        if not ok_phone:
            return

        settings = get_settings()
        db = SessionLocal()
        try:
            face = db.get(UnknownFace, face_id)
            if face is None:
                QMessageBox.warning(self, "Unknown faces", "Record not found.")
                return

            source_path = resolve_stored_path(face.image_path)
            if source_path is None:
                QMessageBox.warning(self, "Unknown faces", "Image file is missing.")
                return

            user = register_person_from_image_file(
                db,
                settings,
                name.strip(),
                source_path,
                phone_number=phone.strip() or None,
            )
            rebuild_embeddings(db, settings)
            delete_unknown_face(db, face_id)
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
            f"Registered {user.full_name} from unknown face #{face_id}.",
        )
        self.load_faces()

    def _delete_selected(self) -> None:
        face_id = self._selected_face_id()
        if face_id is None:
            QMessageBox.information(self, "Unknown faces", "Select a row first.")
            return

        reply = QMessageBox.question(
            self,
            "Delete unknown face",
            f"Delete unknown face record #{face_id}?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        db = SessionLocal()
        try:
            deleted = delete_unknown_face(db, face_id)
        finally:
            db.close()

        if not deleted:
            QMessageBox.warning(self, "Unknown faces", "Could not delete record.")
            return
        self.load_faces()

    def _delete_all(self) -> None:
        reply = QMessageBox.question(
            self,
            "Delete all",
            "Delete all unknown face records and image files?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        db = SessionLocal()
        try:
            removed = delete_all_unknown_faces(db)
        finally:
            db.close()

        QMessageBox.information(
            self,
            "Unknown faces",
            f"Deleted {removed} record(s).",
        )
        self.load_faces()
