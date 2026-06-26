"""Verify run & host utilities."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from app.utils.config import Settings
    from app.utils.network import get_access_urls, get_lan_ip_addresses
    from app.utils.startup import print_startup_banner

    local_urls = get_access_urls("127.0.0.1", 8000)
    if not any("127.0.0.1" in url for _, url in local_urls):
        print("FAIL: local URL missing")
        return 1

    host_urls = get_access_urls("0.0.0.0", 8000)
    if len(host_urls) < 1:
        print("FAIL: host mode should expose URLs")
        return 1
    print(f"Host mode URLs: {len(host_urls)}")

    ips = get_lan_ip_addresses()
    print(f"LAN IPs detected: {len(ips)}")

    for name in ("run.bat", "run_host.bat", "scripts/start_host.ps1", "docs/HOSTING.md"):
        if not (PROJECT_ROOT / name).is_file():
            print(f"FAIL: missing {name}")
            return 1
    print("Run/host scripts: OK")

    print_startup_banner(Settings(host="0.0.0.0", port=8000))
    print("Run & host verification: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
