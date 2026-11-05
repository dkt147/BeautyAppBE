"""Face scan (screens 25 to 28): one photo in, everything the app needs out.

The photo, landmarks and the natural-brow tracing are stored once with a
scan_id, so every later try-on tap only sends ids (no re-upload).
"""
import json
import time

import cv2
import numpy as np

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core import db
from app.core.errors import ApiError
from app.vision import landmarks as LM
from app.vision.brow_measure import (NaturalBrow, brow_shape_label, closest_style, fullness,
                                     measure, read_natural_brow)
from app.vision.face_analysis import (check_quality, classify_face_shape, detect_skin_tone,
                                      face_metrics, nearest_palette_colour)

FEATURE_LINES = {
    "High arch": "A naturally elevated arch.",
    "Defined arch": "A clearly defined arch.",
    "Soft arch": "A softly lifted arch.",
    "Low arch": "A low, gentle arch.",
    "Rounded": "A gently rounded brow.",
    "Straight": "A naturally level line.",
}
# Line 3 of screen 28. Oval is quoted from the screen map; others provisional.
FACE_LINES = {
    "oval": "The kind of face that carries shape with ease.",
    "round": "Soft lines that a lifted arch brings into focus.",
    "square": "Structure that a softer curve balances beautifully.",
    "heart": "Width above that a lower arch keeps calm.",
    "diamond": "Cheekbones that an extended tail frames.",
    "oblong": "Length that a level line brings into balance.",
    "triangle": "A strong jaw that an elevated brow answers.",
}


def scan_dir(scan_id):
    d = config.MEDIA_DIR / "scans" / scan_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _avg_measure(ms):
    keys = [k for k, v in ms[0].items() if isinstance(v, (int, float))]
    out = {k: round(float(np.mean([m[k] for m in ms])), 3) for k in keys}
    kinds = [m["peak_type"] for m in ms]
    out["peak_type"] = kinds[0] if kinds[0] == kinds[1] else "soft"
    return out


def _symmetry(ms):
    a, b = ms
    d = (abs(a["peak_position_pct_from_head"] - b["peak_position_pct_from_head"]) / 30
         + abs(a["peak_height_ew"] - b["peak_height_ew"]) / 0.2
         + abs(a["length_ew"] - b["length_ew"]) / 0.5) / 3
    return round(float(np.clip(1 - d, 0, 1)), 3)


def _brow_bone(lm):
    ew = 0.5 * (LM.eye_width(lm, "left") + LM.eye_width(lm, "right"))
    return float(np.mean([lm[159, 2] - lm[105, 2], lm[386, 2] - lm[334, 2]]) / ew)


def _hair_colour_bgr(image, nb: NaturalBrow):
    ss = np.linspace(nb.head_s + 0.2 * (nb.tail_s - nb.head_s), nb.tail_s - 0.2 * (nb.tail_s - nb.head_s), 30)
    pts = nb.frame.to_image(ss, 0.5 * (nb.top(ss) + nb.bottom(ss)))
    h, w = image.shape[:2]
    px = [image[int(np.clip(p[1], 0, h - 1)), int(np.clip(p[0], 0, w - 1))] for p in pts]
    px = np.array(px, np.float32)
    lum = px.mean(1)
    return np.median(px[lum <= np.percentile(lum, 50)], axis=0)


def recommendation_for(face_shape_id, profile=None, detected_tone=None, natural_colour=None):
    M = load_measurements()
    fs = M.face_shape(face_shape_id)

    def item(sid, role):
        st = M.style(sid)
        pk = M.peak_pct(sid, face_shape_id)
        return {"style": sid, "name": st.name, "role": role,
                "peak_position_pct": pk, "plateau_range_pct": M.plateau(sid, face_shape_id),
                "label": "Recommended for you"}

    profile = profile or {}
    tone = profile.get("skin_tone") or (detected_tone or {}).get("tone") or "medium"
    undertone = profile.get("undertone") or (detected_tone or {}).get("undertone") or "neutral"
    shades = brow_shades(tone, undertone)
    if profile.get("preferred_colour"):
        colour_id, source = profile["preferred_colour"], "your brow profile (screen 15)"
    elif natural_colour:
        # Start from her own brow colour and move one shade toward the best
        # shade for her skin tone (a stylist's "match, then soften").
        ids = [c["id"] for c in C.COLOURS]
        i_n, i_b = ids.index(natural_colour), ids.index(shades["best"])
        step = 0 if i_n == i_b else (1 if i_b > i_n else -1)
        colour_id = ids[i_n + step]
        source = f"your natural brow colour, softened toward skin tone {tone}"
    else:
        colour_id, source = shades["best"], "skin tone " + tone
    direction = C.STYLE_DIRECTIONS.get(profile.get("style_direction") or "", {})
    return {
        "face_shape": face_shape_id,
        "recommended": item(fs.recommended_style, "recommended"),
        "alternate": item(fs.alternate_style, "alternate"),
        "avoid": fs.avoid_styles,
        "peak_adjustment_pts": fs.peak_adjustment_pts,
        "peak_note": fs.peak_note,
        "colour": {**C.COLOUR_BY_ID[colour_id], "source": source},
        "intensity": direction.get("default_intensity", "defined"),
        "mode": direction.get("default_mode", C.DEFAULT_MODE),
    }


def brow_shades(tone, undertone="neutral"):
    m = C.BROW_SHADES_FOR_TONE[tone]
    best, close = m["best"], list(m["close"])
    if undertone == "cool":
        close = [C.COOL_SWAP.get(c, c) for c in close]
        best = C.COOL_SWAP.get(best, best) if tone in ("fair", "light") else best
    return {"best": best, "close": close}


def create_scan(user, data: bytes, face_shape_override=None, profile=None):
    image = LM.decode_image(data)
    faces = LM.detect(image)
    lm, quality = check_quality(image, faces)

    naturals, ms = {}, []
    for side in ("right", "left"):
        nb = read_natural_brow(image, lm, side)
        naturals[side] = nb
        ms.append(measure(nb))
    full = round(float(np.mean([fullness(image, nb) for nb in naturals.values()])), 3)
    if full < 0.05:
        raise ApiError("BROWS_NOT_VISIBLE", "Brow area unobstructed.", 422)

    M = load_measurements()
    metrics = face_metrics(lm)
    detected_shape, trace = classify_face_shape(metrics)
    if face_shape_override:
        if face_shape_override not in M.face_shapes:
            raise ApiError("VALIDATION_ERROR", f"Unknown face shape '{face_shape_override}'.", 422)
    face_shape = face_shape_override or detected_shape

    avg = _avg_measure(ms)
    label = brow_shape_label(avg)
    sym = _symmetry(ms)
    bone = _brow_bone(lm)
    tone = detect_skin_tone(image, lm)
    hair_bgr = np.mean([_hair_colour_bgr(image, nb) for nb in naturals.values()], axis=0)
    natural_colour = nearest_palette_colour(hair_bgr)

    scan_id = db.new_id("scan")
    d = scan_dir(scan_id)
    cv2.imwrite(str(d / "photo.jpg"), image, [cv2.IMWRITE_JPEG_QUALITY, 94])
    np.save(d / "landmarks.npy", lm.astype(np.float32))
    xs, ys = lm[:, 0], lm[:, 1]
    face_box = [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]

    rec = recommendation_for(face_shape, profile, tone, natural_colour)
    sym_line = ("Strong symmetry." if sym >= 0.8 else
                "Balanced symmetry." if sym >= 0.6 else "A natural asymmetry, easy to balance.")
    bone_chip = "STRONG BROW BONE" if bone >= 0.30 else ("DEFINED BROW BONE" if bone >= 0.2 else "SOFT BROW BONE")
    fs_name = M.face_shape(face_shape).name
    doc = {
        "id": scan_id, "user_id": user.id, "created_at": time.time(),
        "image": {"width": image.shape[1], "height": image.shape[0], "path": f"scans/{scan_id}/photo.jpg",
                  "url": config.media_url(f"scans/{scan_id}/photo.jpg")},
        "face_box": face_box,
        "quality": quality,
        "face_shape": {"id": face_shape, "name": fs_name, "tagline": C.FACE_SHAPE_TAGLINES[face_shape],
                       "detected": detected_shape, "source": "override" if face_shape_override else "detected",
                       "metrics": metrics, "rules": trace},
        "brow": {"shape_label": label, "closest_style": closest_style(avg, M.styles),
                 "measurements": {"right": ms[0], "left": ms[1], "average": avg},
                 "symmetry": sym, "fullness": full, "brow_bone": round(bone, 3)},
        "skin_tone_detected": tone,
        "natural_brow_colour": {"id": natural_colour, **C.COLOUR_BY_ID[natural_colour]},
        "recommendation": rec,
        "features": {
            "lines": [FEATURE_LINES[label], sym_line, FACE_LINES[face_shape]],
            "chips": [f"{fs_name.upper()} FACE", label.upper(), bone_chip],
            "ready": "Your recommendations are ready.",
        },
        "natural": {side: {"upper": nb.upper.tolist(), "lower": nb.lower.tolist(),
                           "head_s": nb.head_s, "tail_s": nb.tail_s}
                    for side, nb in naturals.items()},
    }
    db.put("scans", scan_id, user.id, doc)
    return doc


def get_scan(user, scan_id):
    doc = db.get("scans", scan_id)
    if not doc or doc["user_id"] != user.id:
        raise ApiError("SCAN_NOT_FOUND", "That scan was not found. Start a new scan.", 404)
    return doc


def load_scan_assets(doc):
    d = config.MEDIA_DIR / "scans" / doc["id"]
    image = cv2.imread(str(d / "photo.jpg"))
    lm = np.load(d / "landmarks.npy").astype(np.float64)
    naturals = {}
    for side, n in doc["natural"].items():
        naturals[side] = NaturalBrow(side, LM.eye_frame(lm, side), LM.eye_width(lm, side),
                                     np.array(n["upper"]), np.array(n["lower"]), n["head_s"], n["tail_s"])
    return image, lm, naturals


def public_scan(doc):
    """Scan as returned to the app (internal tracing removed)."""
    out = {k: v for k, v in doc.items() if k not in ("natural",)}
    out["scan_id"] = doc["id"]
    out["screen_27"] = {
        "brow_shape": doc["brow"]["shape_label"],
        "face_shape": doc["face_shape"]["name"],
        "recommended_for_you": [doc["recommendation"]["recommended"]["name"],
                                doc["recommendation"]["alternate"]["name"]],
    }
    out["screen_28"] = doc["features"]
    return out
