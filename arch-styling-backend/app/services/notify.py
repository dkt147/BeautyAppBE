"""Outgoing email and SMS (seam for M11).

No email or SMS provider is chosen yet (build plan M11: Postmark, SES or
SendGrid; an SMS provider for screen 65). Until then every message is written
to the `outbox` table and logged without its secret. M11 replaces `_deliver`
and keeps the same `send_email` / `send_sms` calls.
"""
import logging
import time

from app.core import db

log = logging.getLogger("arch.notify")
SENDER = "office@cbygroyals.com"


def _deliver(channel: str, to: str, template: str, data: dict) -> dict:
    msg_id = db.new_id("msg")
    doc = {"id": msg_id, "channel": channel, "to": to, "template": template, "data": data,
           "sender": SENDER, "status": "queued_no_provider", "at": time.time()}
    db.put("outbox", msg_id, data.get("user_id"), doc)
    log.info("outbox %s %s -> %s (%s)", channel, template, to, msg_id)
    return doc


def send_email(to: str, template: str, **data) -> dict:
    return _deliver("email", to, template, data)


def send_sms(to: str, template: str, **data) -> dict:
    return _deliver("sms", to, template, data)


def mask_email(email: str) -> str:
    name, _, domain = email.partition("@")
    return f"{name[:1]}•••@{domain}" if name else email


def mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"···· {digits[-4:]}" if len(digits) >= 4 else phone
