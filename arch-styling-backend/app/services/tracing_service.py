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


# ------------------------------------------------ guide line (client review 19 Nov)

GUIDE_POINTS_PER_EDGE = 32
# A guide point counts as an add zone when it lies outside her natural brow
# (from her scan) by more than this, in eye widths (BACKEND_FIXES item 26).
ADD_ZONE_TOL_EW = 0.03
CENTRE_POINTS = 24


def _ombre_opacity(u: float) -> float:
    """The renderer's Ombre ramp (brow_renderer._ombre_ramp): soft at the
    head, full strength from 60% of the length to the tail."""
    x = min(max(u / 0.6, 0.0), 1.0)
    return round(0.28 + 0.72 * x * x * (3.0 - 2.0 * x), 3)


def guide_strokes(user, sid) -> dict:
    """GET /v1/tracing/sessions/{id}/strokes: the line she traces, placed on
    her own face exactly as the try-on render places the look. The app draws
    it as a thin gold line, not a filled patch."""
    import numpy as np
    from app.rendering.brow_renderer import BrowRenderer
    from app.services.scan_service import load_scan_assets
    from app.vision.landmarks import eye_width

    s = _get(user, sid)
    scan = db.get("scans", s["scan_id"]) if s.get("scan_id") else None
    if not scan or scan.get("user_id") != user.id or not scan.get("natural"):
        raise ApiError("SCAN_REQUIRED", "Scan your face first, so the guide can sit on your brow.", 409)
    r = s["recipe"]
    M = load_measurements()
    face_shape = (scan.get("face_shape") or {}).get("id")
    image, lm, naturals = load_scan_assets(scan)
    h, w = image.shape[:2]
    geos = BrowRenderer().guide(image, lm, M.style(r["style"]), M.peak_pct(r["style"], face_shape),
                                M.plateau(r["style"], face_shape), r["mode"], naturals)
    ombre = r.get("finish") == "ombre"

    def pick(n_pts, total):
        return np.unique(np.linspace(0, total - 1, n_pts).round().astype(int))

    strokes, brows = [], {}
    for side, g in geos.items():
        # One eye width for s_ew / n_ew, always: inner-to-outer corner distance
        # from the scan's own landmarks (EYE[side]: 133-33 right, 362-263 left),
        # the same corners as the frame origin (BACKEND_FIXES item 25c).
        ew = eye_width(lm, side)
        idx = pick(GUIDE_POINTS_PER_EDGE, len(g["u"]))
        ring = list(idx) + list(idx[::-1])                        # top head->tail, then bottom tail->head
        edge = ["top"] * len(idx) + ["bottom"] * len(idx)
        nat = naturals.get(side)
        tol = ADD_ZONE_TOL_EW * ew
        outline = []
        for i, e in zip(ring, edge):
            n = g["top"][i] if e == "top" else g["bottom"][i]
            sv = float(g["s"][i])
            px = g["frame"].to_image(sv, n)
            # add zone: where the guide lies outside her natural brow, read from her scan
            if nat is None:
                kind = "extension"
            elif sv < nat.head_s - tol or sv > nat.tail_s + tol:
                kind = "extension"
            elif (e == "top" and n > float(nat.top(sv)) + tol) or (e == "bottom" and n < float(nat.bottom(sv)) - tol):
                kind = "fill"
            else:
                kind = None
            outline.append({"x": round(float(px[0]) / w, 4), "y": round(float(px[1]) / h, 4),
                            "u": round(float(g["u"][i]), 3), "edge": e,
                            "s_ew": round(sv / ew, 3), "n_ew": round(float(n) / ew, 3),
                            "add_zone": kind is not None, "_kind": kind})
        zones = []
        for k, p in enumerate(outline):                         # contiguous runs along each edge
            if not p["add_zone"]:
                continue
            z = zones[-1] if zones else None
            if z and z["edge"] == p["edge"] and z["_last"] == k - 1:
                z["u_from"], z["u_to"] = min(z["u_from"], p["u"]), max(z["u_to"], p["u"])
                z["kind"] = "extension" if "extension" in (z["kind"], p["_kind"]) else "fill"
                z["_last"] = k
            else:
                zones.append({"edge": p["edge"], "u_from": p["u"], "u_to": p["u"], "kind": p["_kind"], "_last": k})
        for z in zones:
            z.pop("_last")
        for p in outline:
            p.pop("_kind")
        centre = []
        for i in pick(CENTRE_POINTS, len(g["u"])):
            mid = 0.5 * (g["top"][i] + g["bottom"][i])
            px = g["frame"].to_image(g["s"][i], mid)
            u = float(g["u"][i])
            centre.append({"x": round(float(px[0]) / w, 4), "y": round(float(px[1]) / h, 4), "u": round(u, 3),
                           "thickness": round(float(g["top"][i] - g["bottom"][i]) / h, 4),
                           "opacity": _ombre_opacity(u) if ombre else 1.0})
        brows[side] = {"outline": outline, "centre_line": centre, "zones": zones}
        strokes += [{"x": p["x"], "y": p["y"], "brow": side, "u": p["u"], "add_zone": p["add_zone"]}
                    for p in outline]
    return {
        "session_id": s["id"], "type": s["type"], "style": r["style"], "intensity": r.get("intensity"),
        "mode": r["mode"], "finish": r.get("finish") or "full", "scan_id": scan["id"],
        "image": {"width": w, "height": h},
        "coordinates": "x and y are fractions of her scan photo (0,0 top-left, 1,1 bottom-right). "
                       "s_ew and n_ew are the same points in that brow's eye-line frame, in eye widths "
                       "(origin the inner eye corner, s toward the outer corner, n up toward the brow), "
                       "for placing the guide on the live camera with the device's own landmarks.",
        "strokes": strokes,
        "brows": brows,
        "render": {"guide": "thin gold line along each brow's outline; never a filled patch. "
                            "SCULPT (reshape): the whole outline. REFINE (refine): only outline points "
                            "with add_zone true (runs listed in brows.<side>.zones)",
                   "finish": "ombre: hair strokes along centre_line, opacity rising from head (u=0) to tail"
                             if ombre else "full: hair strokes at full opacity"},
    }


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
            "name": name, "caption": name, "editorial_title": None, "mode_label": None,
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
