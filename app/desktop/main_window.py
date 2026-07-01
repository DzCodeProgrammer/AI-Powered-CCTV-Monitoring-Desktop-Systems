"""Main desktop window."""



from __future__ import annotations



from PySide6.QtGui import QCloseEvent

from PySide6.QtWidgets import (

    QHBoxLayout,

    QLabel,

    QMainWindow,

    QTabWidget,

    QVBoxLayout,

    QWidget,

)



from app.desktop.async_runtime import stop_background_tasks

from app.desktop.attendance_panel import AttendancePanel

from app.desktop.model_settings_panel import ModelSettingsPanel

from app.desktop.monitor_panel import MonitorPanel

from app.desktop.register_panel import RegisterPanel

from app.desktop.system_tray import DesktopTray

from app.desktop.unknown_faces_panel import UnknownFacesPanel

from app.models.admin import Admin

from app.services.monitoring_service import shutdown_monitoring

from app.utils.config import get_settings





class MainWindow(QMainWindow):

    def __init__(self, admin: Admin) -> None:

        super().__init__()

        settings = get_settings()

        self.setWindowTitle(f"{settings.app_name} — Desktop")

        self.setMinimumSize(1024, 640)

        self.resize(1200, 720)



        self._admin = admin

        self._monitor = MonitorPanel()

        self._attendance = AttendancePanel()

        self._register = RegisterPanel()

        self._unknown = UnknownFacesPanel()

        self._model_settings = ModelSettingsPanel()



        tabs = QTabWidget()

        tabs.addTab(self._monitor, "Live Monitor")

        tabs.addTab(self._attendance, "Attendance")

        tabs.addTab(self._register, "Register")

        tabs.addTab(self._unknown, "Unknown Faces")

        tabs.addTab(self._model_settings, "Model Settings")



        top = QHBoxLayout()

        title = QLabel(f"Signed in as {admin.username}")

        title.setStyleSheet("font-weight: 600;")

        mode = QLabel(

            f"Mode: {settings.cctv_mode} · Event capture: "

            f"{'on' if settings.event_capture_active else 'off'}"

        )

        mode.setStyleSheet("color: #666; font-size: 12px;")

        top.addWidget(title)

        top.addStretch()

        top.addWidget(mode)



        wrapper = QWidget()

        layout = QVBoxLayout(wrapper)

        layout.addLayout(top)

        layout.addWidget(tabs)

        self.setCentralWidget(wrapper)



        self._tray = DesktopTray(self, self._monitor)

        self._tray.show()



    def closeEvent(self, event: QCloseEvent) -> None:

        self._monitor.shutdown()

        self._tray.hide()

        shutdown_monitoring()

        stop_background_tasks()

        event.accept()


