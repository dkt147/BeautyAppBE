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
from app.core.media import path_of
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
            shutil.copy(config.MEDIA_DIR / path_of(url), ldir / f"{v}.jpg")
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


# ------------------------------------------------------------ 50 rename, 52 share

def rename(look: dict, name=None, tag=None) -> dict:
    if name is not None:
        name = name.strip()
        if not name:
            from app.core.errors import ApiError
            raise ApiError("VALIDATION_ERROR", "Some fields are missing or invalid.", 422,
                           {"details": [{"field": "name", "issue": "Name this look."}]})
        look["name"] = name[:60]
    if tag is not None:
        look["tag"] = tag or None
    db.put("looks", look["id"], look["user_id"], look)
    return decorate(look)


def share_image(look: dict) -> dict:
    """Screen 52: her look with its name and recipe underneath, as one image
    (Save as image / Share via message are native on the phone)."""
    from PIL import Image, ImageDraw, ImageFont

    from app.core.errors import ApiError
    imgs = look.get("images") or {}
    src_url = imgs.get("eyes") or imgs.get("face") or imgs.get("guide")
    if not src_url:
        raise ApiError("PHOTO_REMOVED", "This look has no photograph to share.", 409, {"route_to": None})
    src = Image.open(config.MEDIA_DIR / path_of(src_url)).convert("RGB")
    w = 1080
    src = src.resize((w, max(1, int(src.height * w / src.width))))
    pad, band = 56, 220
    canvas = Image.new("RGB", (w, src.height + band), (10, 10, 10))
    canvas.paste(src, (0, 0))
    d = ImageDraw.Draw(canvas)
    gold, soft = (201, 168, 76), (200, 196, 186)
    d.text((pad, src.height + 40), look["name"], font=ImageFont.load_default(size=44), fill=gold)
    parts = [p for p in (look.get("caption") if look.get("caption") != look["name"] else None,
                         look.get("mode_label")) if p]
    d.text((pad, src.height + 112), "  ·  ".join(parts) or "ARCH", font=ImageFont.load_default(size=28), fill=soft)
    d.text((w - pad - 120, src.height + 160), "ARCH", font=ImageFont.load_default(size=28), fill=gold)
    out_dir = config.MEDIA_DIR / "looks" / look["id"]      # removed with the look's photographs
    out_dir.mkdir(parents=True, exist_ok=True)
    canvas.save(out_dir / "share.jpg", quality=92)
    return {"look_id": look["id"], "image": config.media_url(f"looks/{look['id']}/share.jpg"),
            "title": "Share this look.", "caption": look["name"],
            "line": " · ".join(p for p in (look.get("caption"), look.get("mode_label")) if p),
            "options": [{"id": "save_image", "title": "Save as image", "line": "Saved to your camera roll"},
                        {"id": "share_message", "title": "Share via message", "line": "Opens in your messages app"}],
            "alt": "Back to look", "alt_to": "50"}
