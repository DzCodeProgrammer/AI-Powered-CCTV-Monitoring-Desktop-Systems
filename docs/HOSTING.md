# Run & Host Guide

How to run Smart CCTV on your PC and let other devices on the **same network** access the dashboard.

---

## Quick run (this PC only)

```powershell
.\scripts\start.ps1
```

Or double-click **`run.bat`**.

Open: http://127.0.0.1:8000/login

---

## Host on LAN (phone, tablet, other PC)

### 1. Start in host mode

```powershell
.\scripts\start_host.ps1
```

Or double-click **`run_host.bat`**.

Or set permanently in `.env`:

```env
HOST=0.0.0.0
PORT=8000
```

Then: `python main.py`

### 2. Read the startup banner

After start, the console prints URLs like:

```
  Local              http://127.0.0.1:8000/login
  Network (192.168.1.50)  http://192.168.1.50:8000/login
```

Use the **Network** URL from another device on the same Wi‑Fi/LAN.

### 3. Windows Firewall (if connection refused)

Run **PowerShell as Administrator**:

```powershell
.\scripts\open_firewall.ps1
```

This allows inbound TCP on port `8000` (or your `PORT` in `.env`).

---

## Requirements for hosting

| Item | Note |
|------|------|
| Same network | Phone/PC must be on same Wi‑Fi or LAN as server |
| MySQL running | `docker compose up -d` or native MySQL |
| Strong password | Change `ADMIN_PASSWORD` in `.env` before LAN use |
| Single server | Use one PC as host; do not expose port 8000 to the public internet |

---

## Permanent host via `.env`

```env
HOST=0.0.0.0
PORT=8000
APP_ENV=production
DEBUG=false
```

Restart the app after editing `.env`.

---

## Production (internet-facing)

For public access use **Nginx + HTTPS** — see [DEPLOYMENT.md](DEPLOYMENT.md).  
Do not expose `0.0.0.0:8000` directly to the internet without a reverse proxy and TLS.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Other device cannot connect | Run `open_firewall.ps1`, check same Wi‑Fi |
| Page loads but login fails | Check MySQL is running |
| Wrong IP | Re-read banner after `start_host.ps1` |
| Port in use | Change `PORT=8080` in `.env` |

---

## Related

- [INSTALLATION.md](INSTALLATION.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
