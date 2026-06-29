# WhatsApp notifications

Smart CCTV sends WhatsApp messages via [Fonnte](https://fonnte.com) (third-party API).

## What gets notified

| Event | Recipient | When |
|-------|-----------|------|
| Unknown face detected | `WA_ADMIN_PHONES` | Same interval as detection logging |
| Attendance **Masuk** | User WhatsApp, or **`WA_ADMIN_PHONES`** fallback | **Once** per user, window **07:00–16:59 WIB** |
| Attendance **Pulang** | Same as above | **Once** per user, window **17:00–06:59 WIB** |

Maximum **2 WhatsApp attendance messages per user per day**: one masuk, one pulang.

## Face detection & recognition (dashboard)

On **Live Monitor** (`/dashboard/monitor`):

1. Click **Start monitoring**
2. **Yellow box** — face detected, DeepFace pending
3. **Green box** — recognized (name + confidence) → attendance logged
4. **Red box** — unknown → admin WA alert (if enabled)

Tune interval in **Model settings** (`RECOGNITION_INTERVAL` / `DETECTION_INTERVAL`).

## Setup

1. Register at [fonnte.com](https://fonnte.com) and connect your WhatsApp **device** (scan QR).
2. Copy the **device token** into `.env`:

```env
WA_NOTIFY_ENABLED=true
WA_API_TOKEN=your-device-token
WA_ADMIN_PHONES=628123456789
WA_NOTIFY_UNKNOWN=true
WA_NOTIFY_ATTENDANCE=true
TIMEZONE=Asia/Jakarta
```

3. Or configure from **Dashboard → Model settings → WhatsApp notifications**.
4. Use **Send test message** to verify.
5. Optional: set each person's WhatsApp on **Dashboard → Users** (otherwise admin phone receives attendance).

## Phone number format

- `628123456789` (recommended)
- `08123456789` (auto-converted to 62…)

## Attendance shift (WIB)

| Shift | Local time | WA message |
|-------|------------|--------------|
| **Masuk** | 07:00 – 16:59 | First recognized attendance in this window |
| **Pulang** | 17:00 – 06:59 | First recognized attendance in this window |

Additional recognitions in the same window are still logged in the database but **do not** trigger another WhatsApp message.

## Dahua substream

If the live feed is choppy on an 8 GB laptop:

```env
DAHUA_SUBTYPE=1
```

Or **Model settings → Dahua stream quality → Sub stream**, then **Stop** and **Start** monitoring.
