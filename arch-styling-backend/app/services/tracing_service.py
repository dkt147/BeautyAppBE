"""Tracing sessions and hand-drawn guides (M9): screens 36a, 73 to 77,
45 to 49b.

Live tracing runs on the device. The backend records the session (type,
stage reached, events), applies the gate when it starts, and saves the
result:
  * Reshape mine -> SCULPT (75-01 .. 75-10), Refine mine -> REFINE (76-01 ..
    76-10). The type is fixed when the session starts.
  * 77: if she saved the look on 37 first, the trace attaches to that look;
    otherwise SAVE LOOK creates a new look, which is TRACED.
  * A saved hand-drawn guide (49a, 49b) is a look tagged TRACED.
"""
import json
import time
from datetime import datetime

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core import db
from app.core.errors import ApiError
from app.services import looks_service as LS

TYPES = {"reshape": "sculpt", "refine": "refine"}
STAGE_PREFIX = {"sculpt": "75", "refine": "76"}
STAGE_NAMES = ["Session begins", "First strokes", "Partway", "Stroke drift", "Correction resolved",
               "Zone change", "One brow complete", "Second-brow transition", "Paused · zoomed section",
               "Both brows complete"]
EVENTS = {"interrupted", "resumed", "light_low", "tracking_lost", "hand_occlusion", "recovered",
          "landscape", "portrait", "tracking_failed", "paused"}
MAX_EVENTS = 200


def stages(ttype):
    p = STAGE_PREFIX[ttype]
    return [{"id": f"{p}-{i:02d}", "name": f"{ttype.upper()} · {n}"} for i, n in enumerate(STAGE_NAMES, 1)]


def _get(user, sid):
    s = db.get("tracing_sessions", sid)
    if not s or s["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Tracing session not found.", 404)
    return s


def _save(s):
    db.put("tracing_sessions", s["id"], s["user_id"], s)
    return s


def _public(s):
    return {k: v for k, v in s.items() if k != "events"} | {"event_count": len(s.get("events", []))}


def start(user, recipe: dict, look_id=None, scan=None) -> dict:
    """36a BEGIN. recipe = style, colour, intensity, mode, finish."""
    ttype = TYPES[recipe["mode"]]
    now = time.time()
    sid = db.new_id("trc")
    st = load_measurements().style(recipe["style"])
    s = {"id": sid, "user_id": user.id, "look_id": look_id, "scan_id": scan["id"] if scan else None,
         "type": ttype, "status": "active", "last_stage": None, "stages_reached": [],
         "recipe": recipe, "started_at": now, "ended_at": None, "events": []}
    _save(s)
    return {"session": _public(s), "stages": stages(ttype), "next_screen": "73",
            "you_will_need": [f"A brow pencil in {C.colour_label(recipe['colour'])}",
                              "Good light on your face", "Your phone held steady"],
            "style_measurements": {"length_ew": st.length_ew, "peak_type": st.peak_type,
                                   "peak_position_pct": load_measurements().peak_pct(
                                       recipe["style"], scan["face_shape"]["id"] if scan else None),
                                   "peak_height_ew": st.peak_height_ew,
                                   "thickness_head_ew": st.thickness_head_ew,
                                   "thickness_body_ew": st.thickness_body_ew,
                                   "thickness_tail_ew": st.thickness_tail_ew,
                                   "tail_vs_head_offset_ew": st.tail_offset_ew}}


def update(user, sid, stage=None, event=None, mode=None) -> dict:
    s = _get(user, sid)
    if s["status"] != "active":
        raise ApiError("SESSION_CLOSED", "This tracing session has ended.", 409)
    if mode and TYPES.get(mode) != s["type"]:
        raise ApiError("VALIDATION_ERROR", "The tracing type cannot change once the session has started.", 409)
    if stage:
        ids = [x["id"] for x in stages(s["type"])]
        if stage not in ids:
            raise ApiError("VALIDATION_ERROR", f"Stage {stage} is not part of a {s['type'].upper()} session.", 422)
        if s["last_stage"] and ids.index(stage) < ids.index(s["last_stage"]):
            raise ApiError("VALIDATION_ERROR", "Stages only move forward.", 409)
        s["last_stage"] = stage
        if stage not in s["stages_reached"]:
            s["stages_reached"].append(stage)
    if event:
        if event not in EVENTS:
            raise ApiError("VALIDATION_ERROR", f"Unknown event '{event}'.", 422)
        s["events"] = (s.get("events", []) + [{"event": event, "stage": s["last_stage"], "at": time.time()}])[-MAX_EVENTS:]
    _save(s)
    nxt = {"tracking_failed": "49c", "interrupted": "75a", "light_low": "75b", "tracking_lost": "75c",
           "hand_occlusion": "75e", "recovered": "75f"}.get(event)
    return {"session": _public(s), "next_screen": nxt}


def complete(user, sid) -> dict:
    """75-10 / 76-10 FINISH -> 77. Attaches to the look saved on 37, if any."""
    s = _get(user, sid)
    if s["status"] not in ("active", "completed"):
        raise ApiError("SESSION_CLOSED", "This tracing session has ended.", 409)
    last = stages(s["type"])[-1]["id"]
    if s["last_stage"] != last:
        raise ApiError("VALIDATION_ERROR", f"Finish both brows first (stage {last}).", 409)
    s["status"], s["ended_at"] = "completed", s["ended_at"] or time.time()
    _save(s)
    if s["look_id"] and db.get("looks", s["look_id"]):
        look = LS.decorate(db.get("looks", s["look_id"]))
        return {"session": _public(s), "screen": "77", "state": 2, "look": look,
                "actions": {"view_in_my_looks": "50", "looks_good": "20"}}
    return {"session": _public(s), "screen": "77", "state": 1,
            "actions": {"save_look": "77 state 2", "looks_good": "20"}}


def save_traced_look(user, sid, name=None) -> dict:
    """77 SAVE LOOK (state 1 -> 2): a new look, which is TRACED."""
    s = _get(user, sid)
    if s["status"] != "completed":
        raise ApiError("VALIDATION_ERROR", "Finish the tracing session first.", 409)
    if s["look_id"] and db.get("looks", s["look_id"]):
        return {"session": _public(s), "screen": "77", "state": 2, "look": LS.decorate(db.get("looks", s["look_id"])),
                "actions": {"view_in_my_looks": "50", "looks_good": "20"}}
    scan = db.get("scans", s["scan_id"]) if s["scan_id"] else None
    r = s["recipe"]
    doc, _ = LS.create_look(user, scan, r["style"], r["colour"], r["intensity"], r["mode"], r["finish"], name)
    s["look_id"] = doc["id"]
    _save(s)
    return {"session": _public(s), "screen": "77", "state": 2, "look": LS.decorate(doc),
            "actions": {"view_in_my_looks": "50", "looks_good": "20"}}


def leave(user, sid) -> dict:
    """75d LEAVE SESSION -> 36. Nothing already saved is removed (question 6 open)."""
    s = _get(user, sid)
    if s["status"] == "active":
        s["status"], s["ended_at"] = "left", time.time()
        _save(s)
    return {"session": _public(s), "next_screen": "36", "discarded": [], "question_6_open": True}


# ---------------------------------------------------------- guides (45-49b)

def _date(ts):
    dt = datetime.fromtimestamp(ts)
    return f"{dt.day} {dt:%B %Y}"


def _check_strokes(strokes):
    if not isinstance(strokes, dict) or not any(strokes.get(k) for k in ("left", "right")):
        raise ApiError("VALIDATION_ERROR", "Draw at least one brow before saving.", 422)
    clean = {}
    for side in ("left", "right"):
        lines = strokes.get(side) or []
        if not isinstance(lines, list):
            raise ApiError("VALIDATION_ERROR", f"strokes.{side} must be a list of strokes.", 422)
        out = []
        for line in lines:
            pts = line.get("points") if isinstance(line, dict) else line
            if not isinstance(pts, list) or not all(isinstance(p, (list, tuple)) and len(p) == 2 for p in pts):
                raise ApiError("VALIDATION_ERROR", "Each stroke is a list of [x, y] points (0 to 1).", 422)
            out.append([[round(float(x), 5), round(float(y), 5)] for x, y in pts])
        clean[side] = out
    if sum(len(p) for side in clean.values() for p in side) > 20000:
        raise ApiError("VALIDATION_ERROR", "The guide has too many points.", 422)
    return clean


def save_guide(user, name, strokes, image_bytes=None, image_type=None) -> dict:
    """49a SAVE THIS GUIDE -> 49b. The guide is also a TRACED look in My Looks."""
    clean = _check_strokes(strokes)
    now = time.time()
    gid = db.new_id("gde")
    image = None
    if image_bytes:
        ext = "png" if image_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "jpg"
        if not (ext == "png" or image_bytes[:3] == b"\xff\xd8\xff"):
            raise ApiError("BAD_IMAGE", "Send the guide image as a PNG or JPEG.", 400, {"route_to": None})
        d = config.MEDIA_DIR / "guides" / gid
        d.mkdir(parents=True, exist_ok=True)
        (d / f"guide.{ext}").write_bytes(image_bytes)
        image = config.media_url(f"guides/{gid}/guide.{ext}")
    name = (name or f"Tracing Guide · {_date(now)}").strip()[:60]
    look_id = db.new_id("look")
    look = {"id": look_id, "user_id": user.id, "created_at": now, "scan_id": None, "guide_id": gid,
            "style": None, "colour": None, "intensity": None, "mode": None, "finish": None, "face_shape": None,
            "name": name, "tag": None, "caption": name, "editorial_title": None, "mode_label": None,
            "images": {"guide": image} if image else None}
    db.put("looks", look_id, user.id, look)
    g = {"id": gid, "user_id": user.id, "look_id": look_id, "name": name, "strokes": clean,
         "image": image, "created_at": now}
    db.put("guides", gid, user.id, g)
    return {"guide": g, "look": LS.decorate(look), "screen": "49b",
            "screen_49b": {"title": "Saved.", "line": "This look is in My Looks — ready when you need it.",
                           "cta": "VIEW IT IN MY LOOKS", "cta_to": "50", "tab": "traced",
                           "alt": "Return to home", "alt_to": "20"}}


def get_guide(user, gid):
    g = db.get("guides", gid)
    if not g or g["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Guide not found.", 404)
    return g


def delete_guide(user, gid):
    import shutil
    g = get_guide(user, gid)
    shutil.rmtree(config.MEDIA_DIR / "guides" / gid, ignore_errors=True)
    if g.get("look_id"):
        db.delete("looks", g["look_id"])
    db.delete("guides", gid)
    return {"deleted": gid}


def parse_strokes(raw: str):
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        raise ApiError("VALIDATION_ERROR", "strokes must be JSON: {\"left\": [[[x, y], ...]], \"right\": [...]}", 422)
