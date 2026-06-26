# Session 15 — Final Deliverables

Complete checklist for the **AI-Powered CCTV Monitoring Web System** graduation project.

---

## 1. Complete Source Code

| Layer | Location | Description |
|-------|----------|-------------|
| Entry point | `main.py` | Uvicorn server bootstrap |
| Application factory | `app/__init__.py` | FastAPI app, lifespan, routers |
| HTTP routes | `app/api/routes/` | Auth, dashboard, monitor, registration |
| Business logic | `app/services/` | Auth, registration, detection, export |
| ORM models | `app/models/` | users, admins, detections, attendance, unknown_faces |
| Face AI | `app/face_recognition/` | YuNet/Haar detect, DeepFace match |
| Camera | `app/camera/` | Webcam, RTSP, MJPEG stream |
| Database | `app/database/` | Connection, migrations, init |
| Templates | `app/templates/` | Jinja2 dashboard UI |
| Static assets | `app/static/` | CSS |
| Utilities | `app/utils/` | Config, logging, templates |

---

## 2. Folder Structure

```
smart-cctv/
├── app/                    # Application source
├── scripts/                # Setup, verify, SQL, utilities
├── docs/                   # Full documentation set
├── database/               # SQLite DB + embedding cache (runtime)
├── datasets/               # Registered face images
├── logs/                   # Application logs
├── models/                 # YuNet ONNX model (auto-download)
├── screenshots/            # Detection crops
├── main.py
├── requirements.txt
├── pyproject.toml          # Ruff / PEP8 configuration
├── docker-compose.yml
├── .env.example
└── README.md
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for architecture details.

---

## 3. Database Schema

| Table | Purpose |
|-------|---------|
| `users` | Registered persons + face image paths |
| `admins` | Dashboard administrator accounts |
| `detections` | All face detection events |
| `attendance_logs` | Attendance with deduplication |
| `unknown_faces` | Unknown face gallery crops |

**SQL scripts:**

| File | Purpose |
|------|---------|
| `scripts/init_mysql.sql` | Create database + MySQL user |
| `scripts/schema.sql` | Full `CREATE TABLE` DDL |
| `app/database/migrate.py` | Auto-migrate legacy column names |

Documentation: [DATABASE.md](DATABASE.md)

---

## 4. requirements.txt

Pinned Python dependencies including:

- **Web:** FastAPI, Uvicorn, Jinja2
- **Database:** SQLAlchemy, PyMySQL
- **Auth:** passlib, bcrypt
- **AI:** OpenCV, DeepFace, TensorFlow
- **Export:** openpyxl (Session 14)

Install: `pip install -r requirements.txt`

---

## 5. Documentation

| Document | Content |
|----------|---------|
| [README.md](../README.md) | Project overview & quick start |
| [INSTALLATION.md](INSTALLATION.md) | Step-by-step setup |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Architecture & modules |
| [DATABASE.md](DATABASE.md) | Schema & backup |
| [API.md](API.md) | All routes & responses |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment |

---

## 6. Verification Scripts

Run the full test suite:

```powershell
python scripts\verify_session1.py
python scripts\verify_session2.py
python scripts\verify_session3.py
python scripts\verify_session9.py
python scripts\verify_session10.py
python scripts\verify_session11.py
python scripts\verify_session12.py
python scripts\verify_session13.py
python scripts\verify_session14.py
python scripts\verify_session15.py
python scripts\check_config_security.py
```

---

## 7. Session Completion Map

| Session | Feature |
|---------|---------|
| 1 | Scaffold, FastAPI, MySQL, health check |
| 2 | Admin authentication |
| 3 | Face registration |
| 4 | DeepFace recognition |
| 5 | CCTV monitoring + attendance |
| 6–7 | Dashboard + unknown face gallery |
| 8 | Database schema alignment |
| 9 | `.env` configuration + Dahua RTSP |
| 10 | Error handling + file logging |
| 11 | Performance tuning (low-end hardware) |
| 12 | Full documentation |
| 13 | Code quality (PEP8, type hints, modular) |
| 14 | Excel attendance export |
| 15 | Final deliverables (this document) |

---

## License

[MIT License](../LICENSE) — Copyright (c) 2026 DzCodeProgrammer
