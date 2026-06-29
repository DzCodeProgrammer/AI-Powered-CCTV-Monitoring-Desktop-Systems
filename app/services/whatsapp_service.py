"""WhatsApp notifications via Fonnte API (https://fonnte.com)."""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.user import User
from app.services.attendance_shift import shift_label, should_notify_attendance_wa
from app.utils.config import Settings, get_settings
from app.utils.datetime_local import format_datetime_local
from app.utils.logging import get_logger

logger = get_logger("whatsapp")

FONNTE_SEND_URL = "https://api.fonnte.com/send"
_last_sent: dict[str, float] = {}


def normalize_wa_phone(raw: str) -> str | None:
    if not raw or not str(raw).strip():
        return None
    digits = re.sub(r"\D", "", str(raw).strip())
    if not digits:
        return None
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif not digits.startswith("62"):
        digits = "62" + digits
    return digits if len(digits) >= 10 else None


def parse_admin_phones(settings: Settings) -> list[str]:
    phones: list[str] = []
    for part in settings.wa_admin_phones.split(","):
        normalized = normalize_wa_phone(part)
        if normalized and normalized not in phones:
            phones.append(normalized)
    return phones


def attendance_notify_phones(user: User | None, settings: Settings) -> list[str]:
    """User phone first; fall back to WA_ADMIN_PHONES if user has none."""
    if user and user.phone_number:
        phone = normalize_wa_phone(user.phone_number)
        if phone:
            return [phone]

    admins = parse_admin_phones(settings)
    if not admins and user:
        logger.info(
            "Attendance WA skipped for %s: no phone on user and WA_ADMIN_PHONES empty",
            user.full_name,
        )
    return admins


def _should_send(key: str, interval_seconds: float) -> bool:
    now = time.time()
    last = _last_sent.get(key, 0.0)
    if now - last < interval_seconds:
        return False
    _last_sent[key] = now
    return True


def _format_timestamp(value: datetime) -> str:
    return format_datetime_local(value)


def send_text(settings: Settings | None, target: str, message: str) -> bool:
    settings = settings or get_settings()
    if not settings.wa_notify_enabled or not settings.wa_api_token.strip():
        logger.debug("WhatsApp send skipped: notifications disabled or no token")
        return False

    phone = normalize_wa_phone(target)
    if not phone:
        logger.warning("Invalid WhatsApp target: %s", target)
        return False

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                FONNTE_SEND_URL,
                headers={"Authorization": settings.wa_api_token.strip()},
                data={
                    "target": phone,
                    "message": message,
                    "countryCode": "62",
                },
            )
        if response.status_code >= 400:
            logger.warning(
                "Fonnte API error %s for %s: %s",
                response.status_code,
                phone,
                response.text[:200],
            )
            return False
        logger.info("WhatsApp sent to %s", phone)
        return True
    except Exception as exc:
        logger.warning("WhatsApp send failed to %s: %s", phone, exc)
        return False


def dispatch_whatsapp(func, *args, **kwargs) -> None:
    def _run() -> None:
        try:
            func(*args, **kwargs)
        except Exception as exc:
            logger.warning("Background WhatsApp task failed: %s", exc)

    threading.Thread(target=_run, daemon=True).start()


def notify_unknown_face(
    settings: Settings | None,
    *,
    camera_source: str,
    detected_at: datetime | None = None,
) -> None:
    settings = settings or get_settings()
    if not settings.wa_notify_enabled or not settings.wa_notify_unknown:
        return

    admins = parse_admin_phones(settings)
    if not admins:
        logger.debug("Unknown-face WA skipped: no WA_ADMIN_PHONES configured")
        return

    key = f"unknown:{camera_source}"
    if not _should_send(key, settings.detection_interval):
        return

    when = _format_timestamp(detected_at or datetime.utcnow())
    message = (
        "⚠️ *Smart CCTV — Wajah Tidak Dikenal*\n\n"
        f"Waktu: {when}\n"
        f"Kamera: {camera_source}\n\n"
        "Periksa menu *Unknown Faces* di dashboard."
    )

    for phone in admins:
        dispatch_whatsapp(send_text, settings, phone, message)


def notify_attendance(
    settings: Settings | None,
    db: Session,
    record: Attendance,
    user: User | None,
) -> None:
    settings = settings or get_settings()
    if not settings.wa_notify_enabled or not settings.wa_notify_attendance:
        return
    if not user or not record.user_id:
        logger.info("Attendance WA skipped: user record not found for %s", record.detected_name)
        return

    ok, shift = should_notify_attendance_wa(db, record.user_id, record.detected_at)
    if not ok:
        logger.debug(
            "Attendance WA skipped for %s: already notified this %s window",
            user.full_name,
            shift,
        )
        return

    targets = attendance_notify_phones(user, settings)
    if not targets:
        return

    when = _format_timestamp(record.detected_at or datetime.utcnow())
    confidence = f"{record.confidence * 100:.0f}%" if record.confidence else "-"
    label = shift_label(shift)
    message = (
        f"✅ *Absensi {label} — Smart CCTV*\n\n"
        f"Halo {user.full_name},\n"
        f"Anda tercatat {label.lower()} pada {when}.\n"
        f"Kepercayaan: {confidence}"
    )

    for phone in targets:
        logger.info("Sending attendance %s WA for %s to %s", shift, user.full_name, phone)
        dispatch_whatsapp(send_text, settings, phone, message)


def send_test_message(settings: Settings, target: str) -> tuple[bool, str]:
    if not settings.wa_api_token.strip():
        return False, "WA_API_TOKEN belum diisi."
    phone = normalize_wa_phone(target)
    if not phone:
        return False, "Nomor WhatsApp tidak valid (contoh: 628123456789)."
    ok = send_text(
        settings,
        phone,
        "✅ Smart CCTV — tes notifikasi WhatsApp berhasil.",
    )
    if ok:
        return True, f"Pesan tes terkirim ke {phone}."
    return False, "Gagal mengirim. Periksa token Fonnte dan logs/errors.log."
