"""Login (M1) and membership (M10) are out of scope for the styling build.

`current_user` stands in for real auth:
  * no header            -> the test user (when ARCH_DEV_AUTO_LOGIN=true)
  * X-User-Id: <id>       -> that user (created on first use)
  * X-Guest: true         -> a guest (can browse, cannot scan / try on / save)

`can(user, action)` is the entitlement seam. Today members can do
everything; guests get ACCOUNT_REQUIRED, which routes to screen 13 / 13a.
"""
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Header

from app import config
from app.core import db
from app.core.errors import ApiError


@dataclass
class User:
    id: str
    name: str
    is_guest: bool
    doc: dict


GUEST_ACTIONS = {"browse"}


def _load_or_create(user_id: str, name: str) -> dict:
    doc = db.get("users", user_id)
    if doc is None:
        doc = {"id": user_id, "name": name, "created_at": time.time(),
               "flags": {"mode_intro_seen": False, "onboarding_complete": False}}
        db.put("users", user_id, user_id, doc)
    return doc


def current_user(x_user_id: Optional[str] = Header(None, description="Stub login. Leave empty for the test user."),
                 x_guest: Optional[str] = Header(None, description="Send 'true' to act as a guest.")) -> User:
    if x_guest and x_guest.lower() in ("1", "true", "yes"):
        return User("guest", "Guest", True, {"flags": {}})
    uid = x_user_id or (config.TEST_USER_ID if config.DEV_AUTO_LOGIN else None)
    if not uid:
        return User("guest", "Guest", True, {"flags": {}})
    name = config.TEST_USER_NAME if uid == config.TEST_USER_ID else uid
    doc = _load_or_create(uid, name)
    return User(uid, doc.get("name", name), False, doc)


def can(user: User, action: str) -> bool:
    """Entitlement stub. Replace with the membership check in M10."""
    if user.is_guest:
        return action in GUEST_ACTIONS
    return True


def require(user: User, action: str, gate: str = "13"):
    if not can(user, action):
        raise ApiError("ACCOUNT_REQUIRED",
                       "This needs an account. Create one to continue.", 403,
                       {"route_to": gate})


def save_user(user: User):
    db.put("users", user.id, user.id, user.doc)
