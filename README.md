# AI-Powered CCTV Monitoring Web System

Real-time CCTV monitoring with **face detection**, **face recognition**, **attendance logging**, **Excel export**, and a **web dashboard**.

**Repository:** [github.com/DzCodeProgrammer/AI-Powered-CCTV-Monitoring-Web-Systems](https://github.com/DzCodeProgrammer/AI-Powered-CCTV-Monitoring-Web-Systems)

---

## Features

- Live MJPEG stream — webcam, RTSP, or Dahua IP CCTV
- YuNet + Haar face detection with colored bounding boxes
- DeepFace (Facenet) recognition + unknown face gallery
- Attendance logging with duplicate prevention
- **Export attendance to Excel** (`.xlsx`)
- Admin session authentication
- Optimized for i5 Gen 4 / 8 GB RAM
- Centralized `.env` configuration + file logging

---

## Quick Start

```powershell
git clone https://github.com/DzCodeProgrammer/AI-Powered-CCTV-Monitoring-Web-Systems.git
cd AI-Powered-CCTV-Monitoring-Web-Systems

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
python scripts\generate_secrets.py
docker compose up -d
python scripts\migrate_schema.py
python main.py
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/login | Admin login |
| http://127.0.0.1:8000/dashboard | Overview |
| http://127.0.0.1:8000/dashboard/monitor | Live CCTV |
| http://127.0.0.1:8000/dashboard/attendance/export/preview | Export Excel |
| http://127.0.0.1:8000/api/health | Health check |
| http://127.0.0.1:8000/docs | Swagger UI |

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation Guide](docs/INSTALLATION.md) | Step-by-step setup |
| [Project Structure](docs/PROJECT_STRUCTURE.md) | Architecture & modules |
| [Database Setup](docs/DATABASE.md) | MySQL schema & migrations |
| [API Documentation](docs/API.md) | Routes & responses |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production deployment |
| [Final Deliverables](docs/DELIVERABLES.md) | Session 15 checklist |

**SQL scripts:** [`scripts/init_mysql.sql`](scripts/init_mysql.sql) · [`scripts/schema.sql`](scripts/schema.sql)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Database | MySQL 8.x (SQLite fallback) |
| ORM | SQLAlchemy 2.x |
| Face AI | OpenCV YuNet/Haar, DeepFace Facenet |
| Export | openpyxl |
| Frontend | Jinja2, Bootstrap 5 |

---

## Target Hardware

Intel Core i5 Gen 4 · 8 GB RAM · 128 GB SSD · `LOW_END_MODE=true` (default)

---

## Verification (Sessions 1–15)

```powershell
python scripts\verify_session13.py   # Code quality
python scripts\verify_session14.py   # Excel export
python scripts\verify_session15.py   # Final deliverables
python scripts\check_config_security.py
```

---

## Project Structure

```
smart-cctv/
├── app/                 # Application source (api, services, models, …)
├── scripts/             # SQL, verify, setup utilities
├── docs/                # Full documentation
├── database/            # Embeddings cache (+ SQLite if used)
├── datasets/            # Registered face photos
├── logs/                # app.log, errors.log
├── main.py              # Entry point
├── requirements.txt     # Pinned dependencies
├── pyproject.toml       # Ruff / PEP8 config
└── docker-compose.yml   # MySQL 8.0
```

---

## Security

- `.env` is gitignored — run `python scripts\generate_secrets.py`
- RTSP passwords masked in UI and `/api/health`
- Default bind: `127.0.0.1` (use Nginx for production)

---

## License

[MIT License](LICENSE) — Copyright (c) 2026 DzCodeProgrammer
