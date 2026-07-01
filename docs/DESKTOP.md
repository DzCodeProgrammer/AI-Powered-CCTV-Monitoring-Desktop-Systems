# Smart CCTV — Desktop Monitoring System

Native **PySide6** app for a **single admin laptop**. Reuses the same Python services (OpenCV, DeepFace, MySQL, Dahua events) **without a browser**.

## Why desktop

- No browser / MJPEG overhead — video frames go **directly** to the window
- Single process, single viewer — lower RAM on 8 GB laptops
- `.exe` packaging for demo / skripsi
- **Event-first** mode: Dahua face events run in background; live RTSP only when you click Start

Web mode (`python main.py`) remains available for development.

## Quick start

```powershell
pip install -r requirements.txt -r requirements-desktop.txt
copy .env.example .env
# configure .env (same as web)
python desktop_main.py
```

Or double-click `run_desktop.bat`.

## Features

| Screen | Description |
|--------|-------------|
| Login | Admin username/password (same DB as web) |
| Live Monitor | Direct BGR stream; source picker (CCTV / Webcam) |
| Attendance | Table auto-refresh + **Export Excel** |
| Register | Upload primary + extra training photos, auto-rebuild embeddings |
| Unknown Faces | Gallery, register or delete unknown detections |
| Model Settings | Threshold, interval, frame skip, laptop preset, rebuild embeddings |
| System tray | Start / Stop monitoring, show window, quit |

Background: Dahua event capture + maintenance loop (same as web lifespan).

## Phase 3 desktop defaults

When `CCTV_MODE` / `HOST` are **not** in `.env`, `desktop_main.py` applies:

| Setting | Desktop default | Purpose |
|---------|-----------------|--------|
| `CCTV_MODE` | `event` | CPU-friendly; recognition via Dahua events |
| `HOST` | `127.0.0.1` | No LAN web server (desktop does not start FastAPI) |
| `DESKTOP_DISPLAY_MAX_WIDTH` | `640` | Lower monitor paint cost; AI uses `PROCESS_MAX_WIDTH` |

Single-instance is enforced — only one desktop process (one DeepFace load).

## Build `.exe`

```powershell
pip install -r requirements.txt -r requirements-desktop.txt
scripts\build_desktop.bat
```

Or manually:

```powershell
python -m PyInstaller smart_cctv_desktop.spec --clean
```

Output: `dist/SmartCCTV/SmartCCTV.exe`

Copy your `.env` next to the `.exe` before running.

## Architecture

```text
desktop_main.py
  → desktop env defaults (event mode, display cap)
  → bootstrap (DB, recognition, admin)
  → async_runtime (Dahua events, cleanup)
  → PySide6 UI + system tray
       → MonitorPanel ← get_latest_frame() (display capped at 640px)
       → RegisterPanel / UnknownFacesPanel / ModelSettingsPanel
       → AttendancePanel ← export Excel
```

## Recommended `.env` for desktop-only laptop

```env
HOST=127.0.0.1
CCTV_MODE=event
DESKTOP_DISPLAY_MAX_WIDTH=640
LOW_END_MODE=true
```

Use **Live Monitor → Webcam** for local testing without CCTV network.
