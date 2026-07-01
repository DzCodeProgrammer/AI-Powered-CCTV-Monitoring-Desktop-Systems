"""System tray quick controls for desktop monitoring."""

from __future__ import annotations

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from app.desktop.monitor_controller import monitoring_active, start_desktop_monitoring, stop_desktop_monitoring


class DesktopTray(QSystemTrayIcon):
    def __init__(self, window, monitor_panel) -> None:
        icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        super().__init__(icon)
        self._window = window
        self._monitor = monitor_panel

        self._show_action = QAction("Show window", self)
        self._show_action.triggered.connect(self._show_window)

        self._start_action = QAction("Start monitoring", self)
        self._start_action.triggered.connect(self._start_monitoring)

        self._stop_action = QAction("Stop monitoring", self)
        self._stop_action.triggered.connect(self._stop_monitoring)

        self._quit_action = QAction("Quit", self)
        self._quit_action.triggered.connect(self._quit)

        menu = QMenu()
        menu.addAction(self._show_action)
        menu.addSeparator()
        menu.addAction(self._start_action)
        menu.addAction(self._stop_action)
        menu.addSeparator()
        menu.addAction(self._quit_action)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)
        self._sync_actions()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self) -> None:
        self._window.showNormal()
        self._window.raise_()
        self._window.activateWindow()

    def _start_monitoring(self) -> None:
        if monitoring_active():
            self._sync_actions()
            return
        try:
            source_override = self._monitor.current_source_override()
            start_desktop_monitoring(source_override)
            self._monitor.sync_running_state()
        except Exception as exc:
            self.showMessage("Smart CCTV", f"Could not start monitoring: {exc}")
            return
        self._sync_actions()
        self.showMessage("Smart CCTV", "Monitoring started")

    def _stop_monitoring(self) -> None:
        if not monitoring_active():
            self._sync_actions()
            return
        self._monitor.stop_from_tray()
        self._sync_actions()
        self.showMessage("Smart CCTV", "Monitoring stopped")

    def _quit(self) -> None:
        self._window.close()

    def _sync_actions(self) -> None:
        running = monitoring_active()
        self._start_action.setEnabled(not running)
        self._stop_action.setEnabled(running)
        tooltip = "Smart CCTV — monitoring live" if running else "Smart CCTV — monitoring stopped"
        self.setToolTip(tooltip)

    def refresh(self) -> None:
        self._sync_actions()
