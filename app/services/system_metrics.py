"""Host CPU and memory metrics for dashboard resource widget."""

from __future__ import annotations

from dataclasses import dataclass

import psutil

from app.services.monitoring_service import is_monitoring_active

# Thresholds tuned for 8 GB laptops (e.g. ASUS X455L class hardware).
RAM_WARNING_PERCENT = 85.0
RAM_CRITICAL_PERCENT = 92.0
CPU_WARNING_PERCENT = 88.0
CPU_CRITICAL_PERCENT = 95.0


@dataclass
class SystemMetrics:
    cpu_percent: float
    ram_used_gb: float
    ram_total_gb: float
    ram_available_gb: float
    ram_percent: float
    status: str
    message: str
    monitoring_active: bool
    suggest_stop_monitoring: bool


def _bytes_to_gb(value: float) -> float:
    return round(value / (1024**3), 2)


def get_system_metrics() -> SystemMetrics:
    cpu_percent = float(psutil.cpu_percent(interval=0.1))
    memory = psutil.virtual_memory()

    ram_used_gb = _bytes_to_gb(memory.used)
    ram_total_gb = _bytes_to_gb(memory.total)
    ram_available_gb = _bytes_to_gb(memory.available)
    ram_percent = float(memory.percent)

    monitoring_active = is_monitoring_active()
    suggest_stop = False
    status = "ok"
    message = "Resources look healthy."

    if ram_percent >= RAM_CRITICAL_PERCENT or cpu_percent >= CPU_CRITICAL_PERCENT:
        status = "critical"
        message = "CPU or RAM is very high — stop monitoring to free resources."
        suggest_stop = monitoring_active
    elif ram_percent >= RAM_WARNING_PERCENT or cpu_percent >= CPU_WARNING_PERCENT:
        status = "warning"
        message = "Resources are elevated — consider stopping monitoring if the stream lags."
        suggest_stop = monitoring_active and ram_percent >= RAM_WARNING_PERCENT

    return SystemMetrics(
        cpu_percent=round(cpu_percent, 1),
        ram_used_gb=ram_used_gb,
        ram_total_gb=ram_total_gb,
        ram_available_gb=ram_available_gb,
        ram_percent=round(ram_percent, 1),
        status=status,
        message=message,
        monitoring_active=monitoring_active,
        suggest_stop_monitoring=suggest_stop,
    )


def system_metrics_payload() -> dict:
    metrics = get_system_metrics()
    return {
        "cpu_percent": metrics.cpu_percent,
        "ram_used_gb": metrics.ram_used_gb,
        "ram_total_gb": metrics.ram_total_gb,
        "ram_available_gb": metrics.ram_available_gb,
        "ram_percent": metrics.ram_percent,
        "status": metrics.status,
        "message": metrics.message,
        "monitoring_active": metrics.monitoring_active,
        "suggest_stop_monitoring": metrics.suggest_stop_monitoring,
    }
