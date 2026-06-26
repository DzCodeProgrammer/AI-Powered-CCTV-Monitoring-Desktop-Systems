"""Network helpers for LAN hosting."""

from __future__ import annotations

import socket


def get_lan_ip_addresses() -> list[str]:
    """Return private IPv4 addresses for this machine."""
    addresses: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith("127."):
                continue
            if ip not in addresses:
                addresses.append(ip)
    except OSError:
        pass

    # Fallback: route discovery (works when hostname lookup fails)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if not ip.startswith("127.") and ip not in addresses:
                addresses.append(ip)
    except OSError:
        pass

    return addresses


def get_access_urls(host: str, port: int) -> list[tuple[str, str]]:
    """Build human-readable login URLs for local and network access."""
    urls: list[tuple[str, str]] = []
    urls.append(("Local", f"http://127.0.0.1:{port}/login"))

    if host in {"0.0.0.0", "::"}:
        for ip in get_lan_ip_addresses():
            urls.append((f"Network ({ip})", f"http://{ip}:{port}/login"))
    elif host not in {"127.0.0.1", "localhost"}:
        urls.append(("Configured host", f"http://{host}:{port}/login"))

    return urls
