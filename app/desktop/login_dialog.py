"""Admin login dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.database.connection import SessionLocal
from app.services.auth_service import authenticate_admin
from app.utils.config import get_settings


class LoginDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        settings = get_settings()
        self.setWindowTitle(f"{settings.app_name} — Login")
        self.setMinimumWidth(380)
        self.admin = None

        title = QLabel("Smart CCTV Desktop")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600; margin-bottom: 8px;")

        subtitle = QLabel("Admin sign-in (single laptop)")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 12px;")

        self.username = QLineEdit(settings.admin_username or "admin")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self._try_login)

        form = QFormLayout()
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)

        login_btn = QPushButton("Login")
        login_btn.setDefault(True)
        login_btn.clicked.connect(self._try_login)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(login_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def _try_login(self) -> None:
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Login", "Username and password are required.")
            return

        db = SessionLocal()
        try:
            admin = authenticate_admin(db, username, password)
        finally:
            db.close()

        if admin is None:
            QMessageBox.critical(self, "Login", "Invalid username or password.")
            self.password.clear()
            return

        self.admin = admin
        self.accept()
