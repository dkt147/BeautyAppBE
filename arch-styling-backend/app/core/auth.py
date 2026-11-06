"""Who is calling (M1), and what they may do.

`current_user` reads "Authorization: Bearer <access token>":
  * valid token            -> that account
  * invalid / expired      -> 401 AUTH_REQUIRED (the app refreshes, else opens 08)
  * no token               -> a guest (can browse; gates route to 13 / 13a)
  * X-Guest: true          -> a guest
Tokens issued by the existing auth service (../app/auth, same JWT_SECRET)
are accepted too. Their user is created here on first use.

Dev only (ARCH_DEV_AUTO_LOGIN=true and ARCH_ENV=dev, off by default): no token
means the test user, and "X-User-Id: <id>" acts as that user.

`can(user, action)` is the entitlement seam. Members can do everything until
M10 adds free and member tiers; guests get ACCOUNT_REQUIRED (13 / 13a).
"""
import time
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config
from app.core import db
from app.core.errors import ApiError
from app.core.security import decode_token


@dataclass
class User:
    id: str
    name: str
    is_guest: bool
    doc: dict
    session_id: Optional[str] = None


GUEST_ACTIONS = {"browse"}


def new_user_doc(user_id: str, name: str, **fields) -> dict:
    return {"id": user_id, "name": name, "email": None, "password_hash": None,
            "apple_sub": None, "google_sub": None, "phone": None, "phone_verified": False,
            "two_factor": False, "status": "active", "created_at": time.time(),
            "flags": {"mode_intro_seen": False, "onboarding_complete": False}, **fields}


def _load_or_create(user_id: str, name: str, **fields) -> dict:
    doc = db.get("users", user_id)
    if doc is None:
        doc = new_user_doc(user_id, name, **fields)
        db.put("users", user_id, user_id, doc)
    return doc


def _guest() -> User:
    return User("guest", "Guest", True, {"flags": {}})


def _auth_error(message="Please sign in again."):
    return ApiError("AUTH_REQUIRED", message, 401)


def user_from_token(token: str, allowed_types=("access",)) -> User:
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise _auth_error("Your session has ended. Please sign in again.")
    except jwt.InvalidTokenError:
        raise _auth_error()
    if payload.get("typ") not in allowed_types:
        raise _auth_error()
    sid = payload.get("sid")
    if sid:
        sess = db.get("auth_sessions", sid)
        if not sess or sess.get("revoked_at"):
            raise _auth_error()
    uid = str(payload["sub"])
    doc = db.get("users", uid)
    if doc is None:
        if sid:                                   # our own token for a removed account
            raise _auth_error()
        doc = _load_or_create(uid, "", source="external_auth")   # token from ../app
    if doc.get("status") in ("deleted", "pending_deletion"):
        # pending deletion: sessions were ended; signing in again stops it (5.5)
        raise _auth_error()
    now = time.time()
    if now - (doc.get("last_interaction_at") or 0) > 3600:   # for the retention sweep (M12)
        doc["last_interaction_at"] = now
        db.put("users", uid, uid, doc)
    return User(uid, doc.get("name") or "", False, doc, sid)


_bearer = HTTPBearer(auto_error=False, description="Access token from /v1/auth/register or /v1/auth/login")


def current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
                 x_guest: Optional[str] = Header(None, description="Send 'true' to act as a guest."),
                 x_user_id: Optional[str] = Header(None, include_in_schema=config.DEV_AUTO_LOGIN,
                                                   description="Dev only (ARCH_DEV_AUTO_LOGIN).")) -> User:
    if x_guest and x_guest.lower() in ("1", "true", "yes"):
        return _guest()
    if creds and creds.credentials:
        return user_from_token(creds.credentials.strip())
    if config.DEV_AUTO_LOGIN:
        uid = x_user_id or config.TEST_USER_ID
        name = config.TEST_USER_NAME if uid == config.TEST_USER_ID else uid
        doc = _load_or_create(uid, name)
        return User(uid, doc.get("name", name), False, doc)
    return _guest()


def can(user: User, action: str) -> bool:
    """Entitlements (M10): guest, free account or member."""
    from app.services.billing_service import can as billing_can
    return billing_can(user, action)


def require(user: User, action: str, gate: str = "13"):
    """Guests -> ACCOUNT_REQUIRED (13 / 13a). Free accounts asking for a
    member action (save, trace, guides) -> MEMBERSHIP_REQUIRED (64)."""
    if user.is_guest:
        if action in GUEST_ACTIONS:
            return
        raise ApiError("ACCOUNT_REQUIRED", "This needs an account. Create one to continue.", 403,
                       {"route_to": gate})
    if not can(user, action):
        raise ApiError("MEMBERSHIP_REQUIRED", "This is part of ARCH membership.", 403, {"route_to": "64"})


def save_user(user: User):
    db.put("users", user.id, user.id, user.doc)
