"""Attendance log table for desktop."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.export_service import export_attendance_to_excel, fetch_attendance_records
from app.utils.config import get_settings
from app.utils.datetime_local import format_datetime_local


class AttendancePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        settings = get_settings()

        header = QLabel("Attendance log (latest 100)")
        header.setStyleSheet("font-size: 15px; font-weight: 600;")

        hint = QLabel(
            f"Duplicate entries suppressed for {int(settings.attendance_interval)}s per person."
        )
        hint.setStyleSheet("color: #666; font-size: 12px;")

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Person", "Time (WIB)", "Status", "Confidence", "Camera"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        refresh_btn = QPushButton("Refresh now")
        refresh_btn.clicked.connect(self.load_records)

        export_btn = QPushButton("Export Excel…")
        export_btn.clicked.connect(self._export_excel)

        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(refresh_btn)
        controls.addWidget(export_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(hint)
        layout.addWidget(self._table, stretch=1)
        layout.addLayout(controls)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.load_records)
        self._refresh_timer.start(5000)

        self.load_records()

    def load_records(self) -> None:
        db = SessionLocal()
        try:
            records = fetch_attendance_records(db, limit=100)
        finally:
            db.close()

        self._table.setRowCount(len(records))
        for row, record in enumerate(records):
            name = QTableWidgetItem(record.detected_name)
            when = QTableWidgetItem(
                format_datetime_local(record.detected_at, include_zone=True)
            )
            status = QTableWidgetItem(record.status)
            conf = (
                f"{round(record.confidence * 100)}%"
                if record.confidence is not None
                else "-"
            )
            confidence = QTableWidgetItem(conf)
            camera = QTableWidgetItem(record.camera_source)

            for item in (name, when, status, confidence, camera):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self._table.setItem(row, 0, name)
            self._table.setItem(row, 1, when)
            self._table.setItem(row, 2, status)
            self._table.setItem(row, 3, confidence)
            self._table.setItem(row, 4, camera)

    def _export_excel(self) -> None:
        db = SessionLocal()
        try:
            content, suggested_name = export_attendance_to_excel(db)
        except Exception as exc:
            QMessageBox.critical(self, "Export Excel", f"Export failed:\n{exc}")
            return
        finally:
            db.close()

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save attendance export",
            suggested_name,
            "Excel workbook (*.xlsx)",
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"

        try:
            Path(path).write_bytes(content)
        except OSError as exc:
            QMessageBox.critical(self, "Export Excel", f"Could not save file:\n{exc}")
            return

        QMessageBox.information(self, "Export Excel", f"Saved:\n{path}")
