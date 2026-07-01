# Dahua IPC — FaceDetection Event Capture (Phase 2)

Spesifikasi dari **`Dahua.docx`** (manager): integrasi **kamera IPC langsung**, bukan platform DSS/VMS.

## Model integrasi

Server Smart CCTV **connect ke kamera** (TCP port 80), autentikasi **HTTP Digest**, lalu subscribe stream event:

```http
GET /cgi-bin/snapManager.cgi?action=attachFileProc&channel=1&heartbeat=5
    &Flags[0]=Event&Events=[FaceDetection,EventBaseInfo]
```

Respons: **`multipart/x-mixed-replace`** — bagian bergantian:

| Part | Content-Type | Isi |
|------|--------------|-----|
| Metadata | `text/plain` | `GroupID`, `IndexInGroup`, `Events[0].Code`, `BoundingBox`, `UTC`, … |
| Gambar | `image/jpeg` | Snapshot JPEG |

### Aturan snapshot

- **`IndexInGroup=1`** → frame penuh → diproses recognition
- **`IndexInGroup≥2`** → crop wajah dari kamera → **diabaikan**

Heartbeat kamera: 5 detik. Client timeout baca: 20 detik. Reconnect otomatis: 5 detik.

## Alur di Smart CCTV

```text
[Dahua IPC FaceDetection]
    → DahuaEventSubscriber (HTTP Digest + multipart parser)
    → process_snapshot() — detect + DeepFace sekali per event
    → overlay nama di JPEG
    → log detections + attendance + WA opsional
```

## Konfigurasi `.env`

| Variabel | Default | Keterangan |
|----------|---------|------------|
| `CCTV_MODE` | `hybrid` | `stream` \| `event` \| `hybrid` |
| `DAHUA_EVENT_ENABLED` | `true` | Matikan tanpa ubah mode |
| `DAHUA_HTTP_PORT` | `80` | Port HTTP kamera |
| `DAHUA_EVENT_CHANNEL` | `0` | `0` = pakai `DAHUA_CHANNEL` |
| `DAHUA_EVENT_HEARTBEAT` | `5` | Sesuai query `heartbeat=` |
| `DAHUA_EVENT_TIMEOUT` | `20` | Timeout baca stream (detik) |
| `DAHUA_EVENT_RECONNECT` | `5` | Delay reconnect |

Credential: sama dengan RTSP (`DAHUA_USERNAME`, `DAHUA_PASSWORD`, `DAHUA_HOST`).

## Prasyarat kamera

1. **Face Detection** aktif di web UI kamera Dahua
2. Port **80** reachable dari laptop server
3. User/password HTTP sama dengan RTSP

## Mode operasi

| Mode | RTSP Live Monitor | Event subscriber |
|------|-------------------|------------------|
| `stream` | Ya (Fase 1) | Tidak |
| `event` | Tidak | Ya (Fase 2) |
| `hybrid` | Ya | Ya (disarankan) |

## Status API

`GET /api/health` → field `dahua_events`:

- `enabled`, `connected`, `events_processed`, `last_event_at`, `last_error`

## File implementasi

| Path | Peran |
|------|-------|
| `app/integrations/dahua/subscriber.py` | Subscribe + reconnect loop |
| `app/integrations/dahua/multipart.py` | Parser `multipart/x-mixed-replace` |
| `app/integrations/dahua/metadata.py` | Parse metadata `key=value` |
| `app/services/dahua_event_service.py` | Pipeline recognition + log |
| `app/face_recognition/recognizer.py` | `process_snapshot()` |

## Verifikasi

```bash
python scripts/verify_dahua_events.py
```

Tanpa kamera: uji parser multipart. Dengan kamera: subscriber nyata (opsional).

## Referensi terkait

- **Bukan** untuk Fase 2: `docs/DAHUA_DSS_API_SUMMARY.md` (platform DSS V8.7)
- Fase 1 RTSP: `docs/PHASES.md`
