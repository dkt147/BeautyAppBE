"""Accounts (M1): register, sign in, two-factor, sessions, password reset,
phone, Apple and Google sign-in."""
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from app import config
from app.core import db
from app.core.auth import User, new_user_doc, save_user
from app.core.errors import ApiError
from app.core.security import (codes_match, create_token, hash_code, hash_password, new_code,
                               new_refresh_token, sha256, verify_password)
from app.services import notify


# --------------------------------------------------------------- helpers

def normalise_email(email: str) -> str:
    return email.strip().lower()


def find_by_email(email: str) -> Optional[dict]:
    return db.find_one("users", "email", normalise_email(email))


def public_user(doc: dict) -> dict:
    created = datetime.fromtimestamp(doc.get("created_at") or time.time())
    methods = [m for m, ok in (("password", doc.get("password_hash")), ("apple", doc.get("apple_sub")),
                               ("google", doc.get("google_sub"))) if ok]
    return {"id": doc["id"], "name": doc.get("name") or "", "email": doc.get("email"),
            "phone": doc.get("phone"), "phone_verified": bool(doc.get("phone_verified")),
            "two_factor": bool(doc.get("two_factor")), "sign_in_methods": methods,
            "member_since": f"With us since {created:%B %Y}", "is_guest": False}


def next_screen_after_sign_in(doc: dict) -> str:
    """Screen map: new account -> 14; returning -> 21 when she has a saved
    look, else 20."""
    if not doc.get("flags", {}).get("onboarding_complete"):
        return "14"
    return "21" if db.list_for_user("looks", doc["id"], limit=1) else "20"


def _cancel_pending_deletion(doc: dict) -> bool:
    """Build plan M12 / 5.5: signing in within the 14 days stops deletion."""
    if doc.get("status") == "pending_deletion":
        doc["status"], doc["purge_at"] = "active", None
        db.put("users", doc["id"], doc["id"], doc)
        return True
    return False


# -------------------------------------------------------------- sessions

def start_session(doc: dict, device: Optional[str] = None) -> dict:
    sid = db.new_id("ses")
    refresh = new_refresh_token()
    now = time.time()
    db.put("auth_sessions", sid, doc["id"], {
        "id": sid, "user_id": doc["id"], "refresh_hash": sha256(refresh), "device": device,
        "created_at": now, "last_used_at": now,
        "expires_at": now + config.REFRESH_TOKEN_DAYS * 86400, "revoked_at": None})
    return {"access_token": create_token(doc["id"], "access", sid=sid), "refresh_token": refresh,
            "token_type": "bearer", "expires_in": config.ACCESS_TOKEN_MINUTES * 60}


def signed_in(doc: dict, device=None, is_new=False) -> dict:
    cancelled = _cancel_pending_deletion(doc)
    return {**start_session(doc, device), "user": public_user(doc), "is_new_account": is_new,
            "deletion_cancelled": cancelled, "next_screen": "14" if is_new else next_screen_after_sign_in(doc)}


def refresh_session(refresh_token: str) -> dict:
    sess = db.find_one("auth_sessions", "refresh_hash", sha256(refresh_token))
    if not sess or sess.get("revoked_at") or sess["expires_at"] < time.time():
        raise ApiError("AUTH_REQUIRED", "Please sign in again.", 401)
    doc = db.get("users", sess["user_id"])
    if not doc or doc.get("status") == "deleted":
        raise ApiError("AUTH_REQUIRED", "Please sign in again.", 401)
    new_refresh = new_refresh_token()            # rotate: the old refresh token stops working
    sess.update(refresh_hash=sha256(new_refresh), last_used_at=time.time())
    db.put("auth_sessions", sess["id"], sess["user_id"], sess)
    return {"access_token": create_token(doc["id"], "access", sid=sess["id"]), "refresh_token": new_refresh,
            "token_type": "bearer", "expires_in": config.ACCESS_TOKEN_MINUTES * 60}


def revoke_session(sid: str):
    sess = db.get("auth_sessions", sid)
    if sess and not sess.get("revoked_at"):
        sess["revoked_at"] = time.time()
        db.put("auth_sessions", sid, sess["user_id"], sess)


def revoke_all_sessions(user_id: str, keep: Optional[str] = None):
    for sess in db.list_for_user("auth_sessions", user_id, limit=1000):
        if sess["id"] != keep:
            revoke_session(sess["id"])


# ---------------------------------------------------------- one-time codes

def _otp_id(user_id, purpose):
    return f"{user_id}:{purpose}"


def issue_code(user_id: str, purpose: str, channel: str, destination: str, template: str, **extra) -> dict:
    """Send a 6-digit code. One live code per user and purpose; a resend
    replaces it after the resend wait (screen 11 "Resend in 0:28")."""
    oid = _otp_id(user_id, purpose)
    old = db.get("otp_codes", oid)
    now = time.time()
    if old and not old.get("used") and now - old["sent_at"] < config.OTP_RESEND_SECONDS:
        wait = int(config.OTP_RESEND_SECONDS - (now - old["sent_at"])) + 1
        raise ApiError("RESEND_TOO_SOON", f"You can ask for a new code in {wait} seconds.", 429,
                       {"retry_after": wait})
    code = new_code()
    db.put("otp_codes", oid, user_id, {
        "id": oid, "user_id": user_id, "purpose": purpose, "destination": destination,
        "code_hash": hash_code(code), "sent_at": now, "expires_at": now + config.OTP_MINUTES * 60,
        "attempts": 0, "used": False, **extra})
    if channel == "sms":            # no SMS provider yet (QA item 6): logged, not sent
        notify.send_sms(destination, template, user_id=user_id, code=code, minutes=config.OTP_MINUTES)
    else:
        try:
            notify.send_email(destination, template, required=True, user_id=user_id, code=code,
                              minutes=config.OTP_MINUTES)
        except notify.DeliveryError:
            db.delete("otp_codes", oid)         # so "Resend" works at once
            raise ApiError("EMAIL_NOT_SENT", "We couldn’t send your code. Please try again in a minute.", 503)
    masked = notify.mask_phone(destination) if channel == "sms" else notify.mask_email(destination)
    return {"sent_to": masked, "channel": channel, "resend_after": config.OTP_RESEND_SECONDS,
            "expires_in": config.OTP_MINUTES * 60}


def check_code(user_id: str, purpose: str, code: str) -> dict:
    oid = _otp_id(user_id, purpose)
    otp = db.get("otp_codes", oid)
    if not otp or otp.get("used"):
        raise ApiError("CODE_EXPIRED", "That code has expired. Ask for a new one.", 400)
    if otp["attempts"] >= config.OTP_MAX_ATTEMPTS:
        raise ApiError("CODE_LOCKED", "Too many tries. Ask for a new code.", 429)
    if otp["expires_at"] < time.time():
        raise ApiError("CODE_EXPIRED", "That code has expired. Ask for a new one.", 400)
    if not codes_match(code.strip(), otp["code_hash"]):
        otp["attempts"] += 1
        db.put("otp_codes", oid, user_id, otp)
        left = config.OTP_MAX_ATTEMPTS - otp["attempts"]
        raise ApiError("INVALID_CODE", "That code isn’t right. Please check and try again.", 400,
                       {"attempts_left": left})
    otp["used"] = True
    db.put("otp_codes", oid, user_id, otp)
    return otp


# ---------------------------------------------------------- registration

def check_new_password(password: str, confirm: Optional[str]):
    details = []
    if len(password) < 8:
        details.append({"field": "password", "issue": "Use at least 8 characters."})
    if len(password.encode("utf-8")) > 72:
        details.append({"field": "password", "issue": "Use 72 characters or fewer."})
    if confirm is not None and confirm != password:
        details.append({"field": "confirm_password", "issue": "Passwords do not match"})
    if details:
        raise ApiError("VALIDATION_ERROR", "Some fields are missing or invalid.", 422, {"details": details})


def register(name: str, email: str, password: str, confirm: Optional[str], device=None) -> dict:
    check_new_password(password, confirm)
    email = normalise_email(email)
    if find_by_email(email):
        raise ApiError("EMAIL_REGISTERED", "This email is already linked to an existing account.", 409,
                       {"details": [{"field": "email",
                                     "issue": "This email is already linked to an existing account."}]})
    uid = db.new_id("usr")
    doc = new_user_doc(uid, name.strip(), email=email, password_hash=hash_password(password))
    db.put("users", uid, uid, doc)
    return signed_in(doc, device, is_new=True)


# ---------------------------------------------------------------- sign in

def two_factor_destination(doc: dict):
    if doc.get("phone") and doc.get("phone_verified"):
        return "sms", doc["phone"]
    return "email", doc["email"]


def login(email: str, password: str, device=None) -> dict:
    doc = find_by_email(email)
    if not doc or doc.get("status") == "deleted" or not verify_password(password, doc.get("password_hash")):
        raise ApiError("INVALID_CREDENTIALS", "That email and password don’t match.", 401)
    if doc.get("two_factor"):
        return start_two_factor(doc)
    return signed_in(doc, device)


def start_two_factor(doc: dict) -> dict:
    channel, dest = two_factor_destination(doc)
    sent = issue_code(doc["id"], "2fa", channel, dest, "two_factor_code")
    return {"two_factor_required": True, "next_screen": "11",
            "pending_token": create_token(doc["id"], "2fa_pending", minutes=config.PENDING_2FA_MINUTES),
            **sent}


def verify_two_factor(user: User, code: str, device=None) -> dict:
    check_code(user.id, "2fa", code)
    return signed_in(user.doc, device)


def resend_two_factor(user: User) -> dict:
    channel, dest = two_factor_destination(user.doc)
    return issue_code(user.id, "2fa", channel, dest, "two_factor_code")


# ------------------------------------------------------------- passwords

def forgot_password(email: str) -> dict:
    """Always answers the same way, so it never reveals whether an email has
    an account (screen 10 shows the address she typed)."""
    email = normalise_email(email)
    doc = find_by_email(email)
    if doc and doc.get("status") != "deleted":
        recent = [r for r in db.find_all("otp_codes", "user_id", doc["id"])
                  if r.get("purpose") == "reset" and time.time() - r["sent_at"] < config.OTP_RESEND_SECONDS]
        if not recent:
            token = new_refresh_token()
            rid = "reset:" + sha256(token)
            now = time.time()
            db.put("otp_codes", rid, doc["id"], {
                "id": rid, "user_id": doc["id"], "purpose": "reset", "sent_at": now,
                "expires_at": now + config.RESET_LINK_MINUTES * 60, "used": False})
            notify.send_email(email, "password_reset", user_id=doc["id"],
                              link=reset_link(token), minutes=config.RESET_LINK_MINUTES)
    return {"sent_to": email, "next_screen": "10"}


def reset_link(token: str) -> str:
    """<ARCH_PUBLIC_BASE_URL>/reset-password?token=<token> (QA report item 7)."""
    return f"{config.RESET_LINK_URL}?{urlencode({'token': token})}"


def reset_password(token: str, password: str, confirm: Optional[str]) -> dict:
    check_new_password(password, confirm)
    rid = "reset:" + sha256(token)
    rec = db.get("otp_codes", rid)
    if not rec or rec.get("used") or rec["expires_at"] < time.time():
        raise ApiError("RESET_LINK_INVALID", "This reset link has expired. Ask for a new one.", 400,
                       {"route_to": "09"})
    doc = db.get("users", rec["user_id"])
    if not doc:
        raise ApiError("RESET_LINK_INVALID", "This reset link has expired. Ask for a new one.", 400,
                       {"route_to": "09"})
    for r in db.find_all("otp_codes", "user_id", doc["id"]):    # every open link stops working
        if r.get("purpose") == "reset":
            r["used"] = True
            db.put("otp_codes", r["id"], doc["id"], r)
    doc["password_hash"] = hash_password(password)
    db.put("users", doc["id"], doc["id"], doc)
    revoke_all_sessions(doc["id"])
    return {"password_reset": True, "next_screen": "08"}


def change_password(user: User, current: Optional[str], new: str, confirm: Optional[str]) -> dict:
    if user.doc.get("password_hash") and not verify_password(current or "", user.doc["password_hash"]):
        raise ApiError("INVALID_CREDENTIALS", "Your current password isn’t right.", 401,
                       {"details": [{"field": "current_password", "issue": "Incorrect current password"}]})
    check_new_password(new, confirm)
    user.doc["password_hash"] = hash_password(new)
    save_user(user)
    revoke_all_sessions(user.id, keep=user.session_id)
    return {"password_changed": True}


# ----------------------------------------------------------------- account

def update_me(user: User, name=None, email=None, current_password=None, two_factor=None) -> dict:
    if name is not None:
        if not name.strip():
            raise ApiError("VALIDATION_ERROR", "Some fields are missing or invalid.", 422,
                           {"details": [{"field": "name", "issue": "Enter your name."}]})
        user.doc["name"] = name.strip()
    if email is not None and normalise_email(email) != user.doc.get("email"):
        if user.doc.get("password_hash") and not verify_password(current_password or "", user.doc["password_hash"]):
            raise ApiError("INVALID_CREDENTIALS", "Enter your current password to change your email.", 401,
                           {"details": [{"field": "current_password", "issue": "Incorrect password"}]})
        other = find_by_email(email)
        if other and other["id"] != user.id:
            raise ApiError("EMAIL_REGISTERED", "This email is already linked to an existing account.", 409,
                           {"route_to": None})
        user.doc["email"] = normalise_email(email)
    if two_factor is not None:
        if two_factor and not (user.doc.get("email") or user.doc.get("phone_verified")):
            raise ApiError("VALIDATION_ERROR", "Add an email or a verified phone first.", 422)
        user.doc["two_factor"] = bool(two_factor)
    save_user(user)
    return public_user(user.doc)


def start_phone(user: User, dial_code: str, number: str) -> dict:
    digits = "".join(ch for ch in number if ch.isdigit())
    dial = "+" + "".join(ch for ch in dial_code if ch.isdigit())
    if not (6 <= len(digits) <= 15) or len(dial) < 2:
        raise ApiError("VALIDATION_ERROR", "Some fields are missing or invalid.", 422,
                       {"details": [{"field": "number", "issue": "Enter a valid phone number."}]})
    phone = f"{dial}{digits}"
    return issue_code(user.id, "phone", "sms", phone, "phone_code", phone=phone)


def verify_phone(user: User, code: str) -> dict:
    otp = check_code(user.id, "phone", code)
    user.doc["phone"], user.doc["phone_verified"] = otp["phone"], True
    save_user(user)
    return {"user": public_user(user.doc), "next_screen": "67"}


# -------------------------------------------------------- Apple and Google

APPLE = {"jwks": "https://appleid.apple.com/auth/keys", "iss": ["https://appleid.apple.com"]}
GOOGLE = {"jwks": "https://www.googleapis.com/oauth2/v3/certs",
          "iss": ["accounts.google.com", "https://accounts.google.com"]}
_jwk_clients = {}


def verify_social_token(provider: str, id_token: str) -> dict:
    """Checks the identity token's signature, issuer, audience and expiry
    against the provider's published keys. Returns its claims."""
    import jwt
    audiences = [config.APPLE_CLIENT_ID] if provider == "apple" else config.GOOGLE_CLIENT_IDS
    audiences = [a for a in audiences if a]
    if not audiences:
        raise ApiError("SOCIAL_NOT_CONFIGURED", f"{provider.title()} sign-in is not set up yet.", 503,
                       {"route_to": None})
    spec = APPLE if provider == "apple" else GOOGLE
    try:
        client = _jwk_clients.setdefault(provider, jwt.PyJWKClient(spec["jwks"]))
        key = client.get_signing_key_from_jwt(id_token).key
        claims = jwt.decode(id_token, key, algorithms=["RS256"], audience=audiences,
                            options={"require": ["sub", "exp", "iss"]})
    except jwt.PyJWKClientError:
        raise ApiError("SERVER_ERROR", f"Could not reach {provider.title()} to check the sign-in.", 502)
    except jwt.InvalidTokenError:
        raise ApiError("SOCIAL_TOKEN_INVALID", f"{provider.title()} sign-in didn’t complete. Please try again.", 401)
    if claims.get("iss") not in spec["iss"]:
        raise ApiError("SOCIAL_TOKEN_INVALID", f"{provider.title()} sign-in didn’t complete. Please try again.", 401)
    return claims


def social_sign_in(provider: str, id_token: str, name: Optional[str], device=None) -> dict:
    claims = verify_social_token(provider, id_token)
    sub_field = f"{provider}_sub"
    doc = db.find_one("users", sub_field, claims["sub"])
    is_new = False
    if not doc:
        email = normalise_email(claims["email"]) if claims.get("email") else None
        verified = str(claims.get("email_verified")).lower() == "true"
        doc = find_by_email(email) if (email and verified) else None
        if doc:                                    # same verified email: link to the existing account
            doc[sub_field] = claims["sub"]
        else:
            if email and find_by_email(email):
                raise ApiError("EMAIL_REGISTERED", "This email is already linked to an existing account.", 409)
            uid = db.new_id("usr")
            doc = new_user_doc(uid, (name or claims.get("name") or "").strip(), email=email,
                               **{sub_field: claims["sub"]})
            is_new = True
        db.put("users", doc["id"], doc["id"], doc)
    if doc.get("status") == "deleted":
        raise ApiError("INVALID_CREDENTIALS", "This account is no longer available.", 401)
    if doc.get("two_factor") and not is_new:
        return start_two_factor(doc)
    return signed_in(doc, device, is_new=is_new)
