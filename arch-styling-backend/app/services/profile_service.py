"""Brow profile (screens 14 to 18, later 55): skin tone, goal, direction,
preferred style / colour, remembered mode, last scan."""
import time

from app.catalogue import content as C
from app.core import db

DEFAULT_PROFILE = {
    "skin_tone": None, "undertone": None, "skin_tone_confirmed": False,
    "brow_goal": None, "style_direction": None, "direction_skipped": False,
    "preferred_style": None, "preferred_colour": None,
    # Remembered REFINE MINE / RESHAPE MINE choice, per account (build plan
    # M3). None until she taps the toggle; effective_mode() fills the gap.
    "mode": None,
    # Remembered Full / Ombre for her account (spec Draft 3.2, screen 29).
    # Straight and Micro (Full only) never overwrite it, so her Ombre choice
    # comes back when she returns to a style that has Ombre.
    "finish": None,
    "face_shape": None, "last_scan_id": None, "last_scan_at": None,
    "updated_at": None,
}


def get_profile(user_id):
    doc = db.get("profiles", user_id)
    return {**DEFAULT_PROFILE, **(doc or {})}


def update_profile(user_id, **fields):
    doc = get_profile(user_id)
    doc.update({k: v for k, v in fields.items()})
    doc["updated_at"] = time.time()
    db.put("profiles", user_id, user_id, doc)
    return doc


def effective_mode(profile) -> str:
    """The mode a try-on opens in: the one she last chose, else her style
    direction's default (screen 17), else the client's starting mode
    (Refine mine)."""
    profile = profile or {}
    if profile.get("mode"):
        return profile["mode"]
    direction = C.STYLE_DIRECTIONS.get(profile.get("style_direction") or "", {})
    return direction.get("default_mode") or C.STARTING_MODE


def remember_finish(user_id, style, finish):
    if finish and C.SUPPORTS_OMBRE.get(style) and get_profile(user_id).get("finish") != finish:
        update_profile(user_id, finish=finish)


def remember_mode(user_id, mode):
    if mode and get_profile(user_id).get("mode") != mode:
        update_profile(user_id, mode=mode)


# ------------------------------------------------------- preferences (56, 57)
# A switch must show a state before she touches it. The starting states are
# the ones drawn on screen 56 (Notifications on, Auto-save looks on, Camera
# auto-detect off, English (UK)); each response says which values she set.
PREFERENCE_START = {"notifications_on": True, "auto_save_looks": True, "camera_auto_detect": False,
                    "language": "en-GB"}


def get_preferences(user_id) -> dict:
    stored = (get_profile(user_id).get("preferences") or {})
    out = {k: stored.get(k, v) for k, v in PREFERENCE_START.items()}
    out["set_by_her"] = sorted(k for k in PREFERENCE_START if k in stored)
    return out


def update_preferences(user_id, **fields) -> dict:
    p = get_profile(user_id)
    prefs = dict(p.get("preferences") or {})
    prefs.update({k: v for k, v in fields.items() if v is not None})
    update_profile(user_id, preferences=prefs)
    return get_preferences(user_id)
