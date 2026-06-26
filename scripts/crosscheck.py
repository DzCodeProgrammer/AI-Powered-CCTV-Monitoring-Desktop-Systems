"""Crosscheck: run critical verifications and report summary."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
if not PYTHON.is_file():
    PYTHON = Path(sys.executable)

CHECKS = [
    "verify_session1.py",
    "verify_session2.py",
    "verify_session9.py",
    "verify_session10.py",
    "verify_session11.py",
    "verify_session12.py",
    "verify_session13.py",
    "verify_session14.py",
    "verify_session15.py",
    "check_config_security.py",
]


def main() -> int:
    failed: list[str] = []
    print("Smart CCTV crosscheck\n" + "=" * 40)

    for script in CHECKS:
        path = PROJECT_ROOT / "scripts" / script
        if not path.is_file():
            print(f"SKIP  {script} (missing)")
            continue
        result = subprocess.run(
            [str(PYTHON), str(path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"{status}  {script}")
        if result.returncode != 0:
            failed.append(script)
            tail = (result.stdout + result.stderr).strip().splitlines()
            for line in tail[-3:]:
                print(f"       {line}")

    print("=" * 40)
    if failed:
        print(f"Crosscheck FAILED: {len(failed)} script(s)")
        return 1
    print("Crosscheck OK — all verification scripts passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
