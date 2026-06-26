"""Print server access URLs on startup."""

from __future__ import annotations

from app.utils.config import Settings
from app.utils.network import get_access_urls


def print_startup_banner(settings: Settings) -> None:
    urls = get_access_urls(settings.host, settings.port)
    line = "=" * 54
    print(f"\n{line}")
    print(f"  {settings.app_name}")
    print(f"  Environment: {settings.app_env} | Host: {settings.host}:{settings.port}")
    print(line)
    for label, url in urls:
        print(f"  {label:18} {url}")
    print(f"  {'Dashboard':18} http://127.0.0.1:{settings.port}/dashboard")
    print(f"  {'Health':18} http://127.0.0.1:{settings.port}/api/health")
    if settings.host == "0.0.0.0":
        print("\n  Network mode: other devices on your LAN can open the Network URL.")
        print("  Allow port in Windows Firewall if connection is refused.")
    print(f"{line}\n")
