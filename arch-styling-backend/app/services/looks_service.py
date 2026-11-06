"""Saved looks (M8 core, shared by 37, 77 and 49a).

A look stores one name, the recipe (style, intensity, colour, mode, finish)
and its photographs (nullable: Delete my face scan can remove them). Its
TRACED / PREVIEWED kind is derived from whether a completed tracing session
or a saved guide points at it (F11), so it can never disagree with the data.
"""
import shutil
import time
from datetime import datetime

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core import db
from app.services import render_service as RS


def _date(ts):
    dt = datetime.fromtimestamp(ts)
    return f"{dt.day} {dt:%B %Y}"


def create_look(user, scan, style, colour, intensity, mode, finish, name=None, tag=None, extra=None):
    look_id = db.new_id("look")
    images = None
    if scan is not None:
        r = RS.render(user, scan, style, colour, intensity, mode, ["full", "face", "eyes"], finish=finish)
        ldir = config.MEDIA_DIR / "looks" / look_id
        ldir.mkdir(parents=True, exist_ok=True)
        images = {}
        for v, url in r["images"].items():
            shutil.copy(config.MEDIA_DIR / url.split("/media/", 1)[1], ldir / f"{v}.jpg")
            images[v] = config.media_url(f"looks/{look_id}/{v}.jpg")
    copy = RS.look_copy(style, colour, intensity, mode, finish)
    doc = {"id": look_id, "user_id": user.id, "created_at": time.time(),
           "scan_id": scan["id"] if scan else None,
           "style": style, "colour": colour, "intensity": intensity, "mode": mode, "finish": finish,
           "face_shape": scan["face_shape"]["id"] if scan else None,
           "name": (name or copy["caption"]).strip(), "tag": tag,
           "caption": copy["caption"], "editorial_title": copy["editorial_title"],
           "mode_label": copy["mode_label"], "images": images, **(extra or {})}
    db.put("looks", look_id, user.id, doc)
    return doc, copy


def kind(look: dict) -> str:
    if look.get("guide_id"):
        return "traced"
    for s in db.find_all("tracing_sessions", "look_id", look["id"]):
        if s.get("status") == "completed":
            return "traced"
    return "previewed"


def decorate(look: dict) -> dict:
    out = dict(look)
    out["kind"] = kind(look)
    out["kind_label"] = out["kind"].upper()
    if look.get("style"):
        style = load_measurements().style(look["style"]).name
        out["saved_label"] = f"{_date(look['created_at'])} · {style} · {C.colour_label(look['colour'])}"
    else:
        out["saved_label"] = _date(look["created_at"])
    out["saved_line"] = f"Saved {_date(look['created_at'])}" + (
        f" · {look['mode_label']}" if look.get("mode_label") else "")
    return out


def list_for(user_id: str, tab: str = "all") -> list:
    looks = [decorate(lk) for lk in db.list_for_user("looks", user_id, limit=1000)]
    if tab in ("traced", "previewed"):
        looks = [lk for lk in looks if lk["kind"] == tab]
    return looks
