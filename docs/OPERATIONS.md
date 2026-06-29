# Operations — schedule, cleanup, auto-start

Laptop-friendly settings to reduce CPU heat, save disk space on HDD, and run the server after Windows boot.

## Monitoring schedule

Automatically start/stop live monitoring by time of day (e.g. **07:00–17:00** for office hours).

1. Open **Dashboard → Model settings** (bottom section **Operations**).
2. Enable **automatic monitoring schedule**, set start/stop times, click **Save operations**.

The server checks every 60 seconds. Outside the window, monitoring stops and the camera is released (less CPU/heat).

Configure in `.env`:

```env
MONITOR_SCHEDULE_ENABLED=true
MONITOR_SCHEDULE_START=07:00
MONITOR_SCHEDULE_END=17:00
```

## Disk cleanup

Deletes old files in `logs/` (`.log`) and `screenshots/` (images) by age.

| Setting | Default | Meaning |
|---------|---------|---------|
| `CLEANUP_ENABLED` | `true` | Run periodic cleanup |
| `LOG_RETENTION_DAYS` | `30` | Keep logs this many days |
| `SCREENSHOT_RETENTION_DAYS` | `14` | Keep screenshots this many days |
| `CLEANUP_INTERVAL_HOURS` | `24` | How often to run (hours) |

Use **Run cleanup now** on the Model settings page for immediate cleanup.

## Windows auto-start

Start the server at login without opening a terminal:

```powershell
.\scripts\install_autostart.ps1
```

- Creates a shortcut in your **Startup** folder (hidden PowerShell window).
- Logs to `logs/autostart.log`.
- Starts Docker/MySQL if available, runs migrations, then `main.py`.

Remove:

```powershell
.\scripts\uninstall_autostart.ps1
```

**Note:** After reboot, open `http://127.0.0.1:8000` (or your LAN IP if `HOST=0.0.0.0`). Monitoring still follows the schedule — it does not force-start outside the window unless you enable the schedule and are inside the window.

## Manual run (reference)

| Script | Use |
|--------|-----|
| `.\scripts\start.ps1` | Local only (`127.0.0.1`) |
| `.\scripts\start_host.ps1` | LAN host (`HOST=0.0.0.0`) |
| `run.bat` / `run_host.bat` | Double-click from Explorer |
