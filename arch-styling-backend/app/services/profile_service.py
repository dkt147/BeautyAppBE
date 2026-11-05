"""Brow profile (screens 14 to 18, later 55): skin tone, goal, direction,
preferred style / colour, last scan."""
import time

from app.core import db

DEFAULT_PROFILE = {
    "skin_tone": None, "undertone": None, "skin_tone_confirmed": False,
    "brow_goal": None, "style_direction": None, "direction_skipped": False,
    "preferred_style": None, "preferred_colour": None,
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
