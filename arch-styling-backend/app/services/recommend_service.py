"""Recommendations (M6): screens 41, 42 and 43, from her latest scan.

Spec Draft 3.2: screen 41 is retired. It is kept in place until the client
confirms in writing that one scan produces both the brow profile and the
recommendation data (it does: see scan_service). The face shape used is the
one on her brow profile (55a lets her set it), else the scan's.

Table 2 of the Measurement Reference gives exactly two styles per face shape
(recommended, alternate). The app adds her own pick as a third chip
(question 12, decided). Nothing defaults to Arch or Structured.
"""
import cv2
import numpy as np

from app import config
from app.catalogue import content as C
from app.catalogue import recommend_copy as RC
from app.catalogue.measurements import load_measurements
from app.core import db
from app.core.errors import ApiError
from app.services import library_service as L
from app.services import render_service as RS
from app.services.profile_service import get_profile
from app.services.scan_service import scan_dir


def latest_scan(user):
    rows = db.list_for_user("scans", user.id, limit=1)
    if not rows:
        raise ApiError("SCAN_REQUIRED", "Scan your face first to see what suits you.", 409)
    return rows[0]


def face_shape_of(user, scan) -> str:
    """55a: the face shape she saves is the one used for recommendations."""
    return get_profile(user.id).get("face_shape") or scan["face_shape"]["id"]


def _tone(user, scan):
    p = get_profile(user.id)
    return p.get("skin_tone") or (scan.get("skin_tone_detected") or {}).get("tone")


def _style_item(sid, role, face, tone, label=None):
    M = load_measurements()
    return {"style": sid, "name": M.style(sid).name, "role": role, "label": label,
            "reading": C.STYLE_READINGS[sid], "peak_position_pct": M.peak_pct(sid, face),
            "image": L.image("full", tone, sid, "defined") if tone else None,
            "diagram_url": f"/v1/styles/{sid}/diagram.png?face_shape={face}"}


def recommendations(user) -> dict:
    """Screen 41."""
    sc = latest_scan(user)
    M = load_measurements()
    face = face_shape_of(user, sc)
    fs = M.face_shape(face)
    tone = _tone(user, sc)
    items = [_style_item(fs.recommended_style, "recommended", face, tone, "Top recommendation"),
             _style_item(fs.alternate_style, "alternate", face, tone)]
    pick = get_profile(user.id).get("preferred_style")
    return {
        "scan_id": sc["id"], "screen": "41", "retired": True,
        "face_shape": {"id": face, "name": fs.name, "tagline": C.FACE_SHAPE_TAGLINES[face]},
        "title": f"Your face shape: {fs.name}",
        "photo": RS.before_images(sc).get("face"),
        "recommendations": items,
        "your_pick": (_style_item(pick, "your_pick", face, tone)
                      if pick and pick not in (fs.recommended_style, fs.alternate_style) else None),
        "avoid": fs.avoid_styles,
        "peak_adjustment_pts": fs.peak_adjustment_pts, "peak_note": fs.peak_note,
        "line": "Tailored to your features. You lead from here.",
        "cta": "TRY TOP RECOMMENDATION", "cta_to": "42", "cta_route_to_confirm": True,
        "alt": "See all styles", "alt_to": "29",
    }


def _outline(sc):
    """The face-oval outline on her own photo, in the 43 crop."""
    d = scan_dir(sc["id"])
    lm = np.load(d / "landmarks.npy").astype(np.float64)
    pts = lm[RC.FACE_OVAL, :2]
    box = RS._boxes(sc, lm)["face"]
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    norm = [[round(float((x - x0) / w), 4), round(float((y - y0) / h), 4)] for x, y in pts]
    (cx, cy), (ew, eh), ang = cv2.fitEllipse(pts.astype(np.float32))
    out = d / "outline_43.jpg"
    if not out.exists():
        img = cv2.imread(str(d / "photo.jpg"))
        crop = RS._crop(img, box).copy()
        off = np.array([max(0, int(round(x0))), max(0, int(round(y0)))])
        gold = (76, 168, 201)
        cv2.ellipse(crop, ((cx - off[0], cy - off[1]), (ew, eh), ang), gold, 2, cv2.LINE_AA)
        cv2.polylines(crop, [(pts - off).astype(np.int32)], True, (90, 190, 220), 1, cv2.LINE_AA)
        cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return {"points": norm,
            "ellipse": {"cx": round((cx - x0) / w, 4), "cy": round((cy - y0) / h, 4),
                        "width": round(ew / w, 4), "height": round(eh / h, 4), "angle": round(float(ang), 2)},
            "length_to_width": round(float(max(ew, eh) / max(1e-6, min(ew, eh))), 3),
            "image": config.media_url(f"scans/{sc['id']}/outline_43.jpg")}


def why(user, style=None) -> dict:
    """Screens 42 (view 1) and 43 (view 2). The words are per face shape
    (spec Draft 3.2); the heading of 42 is the style her face shape
    recommends. Any other style has no client copy for 42 yet."""
    sc = latest_scan(user)
    M = load_measurements()
    face = face_shape_of(user, sc)
    fs = M.face_shape(face)
    style = style or fs.recommended_style
    if style not in C.STYLE_ORDER:
        raise ApiError("VALIDATION_ERROR", f"Unknown style '{style}'.", 422)
    c42, c43 = RC.screen_42(face), RC.screen_43(face)
    written = style == c42["heading_style"]
    tone = _tone(user, sc)
    return {
        "scan_id": sc["id"], "style": style, "face_shape": face,
        "fit": ("recommended" if style == fs.recommended_style else "alternate" if style == fs.alternate_style
                else "avoid" if style in fs.avoid_styles else "neutral"),
        "screen_42": {"title": M.style(style).name, "label": "ABOUT THIS SHAPE",
                      "image": L.image("full", tone, style, "defined") if tone else None,
                      "points": c42["lines"] if written else None, "copy_written": written,
                      "cta": "WHY IT SUITS YOUR FACE", "cta_to": "43", "alt": "Try another", "alt_to": "29",
                      "back_to": "27"},
        "screen_43": {"label": "WHY THIS SHAPE SUITS YOUR FACE", "photo": RS.before_images(sc).get("face"),
                      "outline": _outline(sc), "headline": c43["headline"], "body": c43["body"],
                      "title": " ".join(c43["headline"]), "body_text": " ".join(c43["body"]),
                      "tagline": c43["tagline"], "closing": c43["tagline"],
                      "cta": "SEE THE DIFFERENCE", "cta_to": "44",
                      "alt": "Try a different recommendation", "alt_to": "27", "back_to": "42"},
    }
