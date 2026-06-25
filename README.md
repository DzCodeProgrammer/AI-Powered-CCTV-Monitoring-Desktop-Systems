# AI-Powered CCTV Monitoring System

Production-style real-time CCTV monitoring with face detection, recognition, attendance logging, and a web dashboard.

**Repository:** [github.com/DzCodeProgrammer/AI-Powered-CCTV-Monitoring-System](https://github.com/DzCodeProgrammer/AI-Powered-CCTV-Monitoring-System)

## Session 1 Status (Complete)

- Clean architecture folder structure
- FastAPI application skeleton
- SQLAlchemy ORM models (`users`, `detections`, `unknown_faces`)
- MySQL database (native or Docker Compose)
- SQLite fallback (optional)
- Health check API at `/api/health`
- Security hardening scripts

## Prerequisites

- Python 3.11+
- pip
- MySQL 8.x (native install or Docker Compose)

## Quick Start

### 1. Clone & setup

```powershell
git clone https://github.com/DzCodeProgrammer/AI-Powered-CCTV-Monitoring-System.git
cd AI-Powered-CCTV-Monitoring-System

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Secure configuration

```powershell
copy .env.example .env
python scripts\generate_secrets.py
.\scripts\secure_mysql.ps1
```

This generates strong `SECRET_KEY`, `MYSQL_ROOT_PASSWORD`, and `DB_PASSWORD` in `.env` (never committed).

### 3. Start MySQL

**Docker:**

```powershell
docker compose up -d
docker compose ps
```

**Native MySQL:** ensure service is running, then run `scripts\secure_mysql.ps1`.

### 4. Run application

```powershell
python main.py
```

Open: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

Verify database:

```powershell
python scripts\verify_session1.py
```

## Security

| Practice | Status |
|----------|--------|
| `.env` in `.gitignore` | Yes |
| Strong secrets via `generate_secrets.py` | Yes |
| MySQL root password set | Via `secure_mysql.ps1` |
| App binds to `127.0.0.1` by default | Yes |
| MySQL Docker port bound to localhost | Yes |
| `DEBUG=false` by default | Yes |

**Never commit `.env` or real passwords.** Use `.env.example` placeholders only.

## Project Structure

```
smart-cctv/
├── app/
│   ├── api/              # REST routes
│   ├── services/         # Business logic (Session 2+)
│   ├── models/           # SQLAlchemy ORM models
│   ├── database/         # DB connection & session
│   ├── face_recognition/ # Face processing (Session 2+)
│   ├── camera/           # Webcam / RTSP (Session 2+)
│   ├── templates/        # Jinja2 dashboard (Session 3)
│   ├── static/           # CSS, JS, assets
│   └── utils/            # Config & helpers
├── scripts/              # Setup & security helpers
├── datasets/             # Registered face images
├── logs/                 # Application logs
├── screenshots/          # Detection snapshots
├── docker-compose.yml    # MySQL 8.0 service
├── main.py               # Entry point
└── requirements.txt
```

## Database

Tables (`users`, `detections`, `unknown_faces`) are created automatically on first startup.

### SQLite fallback (optional)

```env
DB_DRIVER=sqlite
```

## Roadmap

| Session | Focus |
|---------|-------|
| **1** | Scaffold, FastAPI, SQLAlchemy, MySQL, health check |
| **2** | Face recognition, camera stream, register-face API |
| **3** | Web dashboard (Jinja2 + Bootstrap 5) |
| **4** | RTSP IP CCTV, unknown face alerts |
| **5** | Production deployment |

## License

MIT
