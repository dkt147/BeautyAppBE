"""Outgoing email, SMS and push (M11, QA report item 6).

Email is sent over SMTP with the SMTP_* settings (config.py / .env). Nothing
is stored: codes and reset links only exist in the message itself. SMS and
push have no provider yet, so they are logged (without their content) and
reported as not sent.

Every message goes through `transport(message)`, the one place that talks to
the outside world. The tests replace it to read the codes they need.
"""
import logging
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from app import config
from app.core import db

log = logging.getLogger("arch.notify")


class DeliveryError(Exception):
    """A message that had to go out could not be sent."""


# ------------------------------------------------------------- templates
# subject, body. Bodies are plain text; {fields} come from the send_* call.
TEMPLATES = {
    "two_factor_code": ("Your ARCH sign-in code",
                        "Your ARCH sign-in code is {code}.\n\nIt expires in {minutes} minutes. "
                        "If you didn’t try to sign in, change your password."),
    "phone_code": ("Your ARCH code", "Your ARCH code is {code}. It expires in {minutes} minutes."),
    "password_reset": ("Reset your ARCH password",
                       "Tap the link below to set a new password. It expires in {minutes} minutes.\n\n"
                       "{link}\n\nIf you didn’t ask for this, you can ignore this email; "
                       "your password won’t change."),
    "account_deletion": ("Your ARCH account will be deleted",
                         "We’ve received your request to delete your ARCH account. Your account and "
                         "everything in it will be permanently deleted on {purge_date}.\n\n"
                         "Changed your mind? Sign in before then to keep your account."),
    "support_message": ("ARCH support message from {name}",
                        "From: {name} <{reply_to}>\nMessage id: {message_id}\n\n{body}"),
    "trial_started": ("Your ARCH free trial has started",
                      "Welcome to {plan}. Your free trial runs until {period_end}."),
    "trial_ending": ("Your ARCH free trial ends soon",
                     "Your free trial of {plan} ends on {date}. Your membership starts then "
                     "unless you cancel before."),
    "payment_failed": ("We couldn’t take your ARCH payment",
                       "We couldn’t renew {plan}. Please update your payment details so your "
                       "membership continues."),
    "payment_confirmed": ("Your ARCH membership is active",
                          "Thank you. {plan} is active until {period_end}."),
    "membership_cancelled": ("Your ARCH membership is cancelled",
                             "{plan} is cancelled. You keep access until {period_end}."),
    "annual_renewal": ("Your ARCH membership renews soon", "{plan} renews on {date}."),
    "monthly_anniversary": ("Your ARCH membership renews soon", "{plan} renews on {date}."),
}


class _Blank(dict):
    def __missing__(self, key):
        return ""


def render(template: str, data: dict) -> tuple:
    subject, body = TEMPLATES.get(template, ("ARCH", "{template}"))
    fields = _Blank({k: ("" if v is None else v) for k, v in data.items()}, template=template)
    return subject.format_map(fields), body.format_map(fields) + "\n\nARCH\n"


# ------------------------------------------------------------- transport

def smtp_configured() -> bool:
    return bool(config.SMTP_HOST)


def smtp_send(to: str, subject: str, body: str, reply_to: str = None) -> str:
    """Send one plain-text email. Returns the Message-ID; raises on failure."""
    msg = EmailMessage()
    msg["From"] = formataddr((config.SMTP_FROM_NAME, config.SMTP_FROM))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=config.SMTP_FROM.partition("@")[2] or None)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    ctx = ssl.create_default_context()
    if config.SMTP_TLS == "ssl":
        server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=config.SMTP_TIMEOUT, context=ctx)
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=config.SMTP_TIMEOUT)
    with server:
        if config.SMTP_TLS == "starttls":
            server.starttls(context=ctx)
        if config.SMTP_USER:
            server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)
    return msg["Message-ID"]


def transport(message: dict) -> str:
    """Deliver one message. Returns "sent", "not_configured" or "no_provider";
    raises on a failed send."""
    if message["channel"] != "email":
        log.warning("%s %s -> %s not sent: no %s provider yet", message["channel"], message["template"],
                    message["to"], message["channel"])
        return "no_provider"
    if not smtp_configured():
        log.error("email %s -> %s not sent: SMTP_HOST is not set", message["template"], message["to"])
        return "not_configured"
    subject, body = render(message["template"], message["data"])
    smtp_send(message["to"], subject, body, reply_to=message["data"].get("reply_to"))
    log.info("email %s -> %s sent", message["template"], message["to"])
    return "sent"


def _deliver(channel: str, to: str, template: str, data: dict, required: bool) -> dict:
    message = {"channel": channel, "to": to, "template": template, "data": data, "at": time.time()}
    try:
        status = transport(message)
    except Exception as exc:                     # SMTP refused, timed out, bad login...
        log.error("%s %s -> %s failed: %s", channel, template, to, exc)
        if required:
            raise DeliveryError(str(exc)) from exc
        status = "failed"
    if required and status != "sent":
        raise DeliveryError(status)
    return {"channel": channel, "to": to, "template": template, "status": status}


def send_email(to: str, template: str, required: bool = False, **data) -> dict:
    """required=True raises DeliveryError unless the email really went out."""
    return _deliver("email", to, template, data, required)


def send_sms(to: str, template: str, required: bool = False, **data) -> dict:
    return _deliver("sms", to, template, data, required)


def send_push(user_id: str, template: str, **data) -> list:
    """Push to every registered device, only when the Notifications switch
    on 56 is on. No FCM / APNs credentials yet: logged, not sent."""
    from app.services.profile_service import get_preferences
    if not get_preferences(user_id)["notifications_on"]:
        return []
    out = []
    for dev in db.list_for_user("devices", user_id, limit=50):
        if dev.get("permission") != "denied":
            out.append(_deliver("push", dev["id"], template,
                                {"user_id": user_id, "platform": dev["platform"], **data}, False))
    return out


def mask_email(email: str) -> str:
    name, _, domain = email.partition("@")
    return f"{name[:1]}•••@{domain}" if name else email


def mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"···· {digits[-4:]}" if len(digits) >= 4 else phone
