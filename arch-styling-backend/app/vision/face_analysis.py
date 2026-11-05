"""Face shape, photo quality and skin tone from the 478 landmarks.

FACE SHAPE follows the client's classifier (master reference, Part C) in its
exact order: Oblong, Round, Diamond, Heart, Triangle, Square, then Oval as
the catch-all.

The client's thresholds (H:W > 1.75, FW/JW > 1.15, FW/JW < 0.85, ...) are
written for real tape-measure proportions with the hairline as the top of
the face. MediaPipe's mesh has no hairline point and is a smoothed 3-D
model, so raw mesh ratios sit in a much narrower band. CALIBRATION maps mesh
ratios onto the client's scale before the client's thresholds are applied.
The calibration values were set on a small set of test photos and must be
checked by the client on real ARCH users (see README, "Known limits").
"""
import cv2
import numpy as np

from app.catalogue.content import SKIN_TONES, COLOURS
from app.core.errors import ApiError

CALIBRATION = {
    # landmark 10 sits below the hairline; real face height ~ 1.33x mesh height
    "height_factor": 1.33,
    # mesh FW/JW spread is about half the real spread; centre 1.07 -> 1.05
    "fw_jw_centre_mesh": 1.07,
    "fw_jw_centre_true": 1.05,
    "fw_jw_gain": 2.0,
}

RULES = {
    "oblong_hw_min": 1.75,          # client: H:W > 1.75
    "round_hw_max": 1.53,           # client: W:H ~ 1.0 (calibrated)
    "round_jaw_curve_min": 0.70,    # client: jaw curve > 0.7
    "diamond_fw_w_max": 0.815,      # cheekbones clearly widest
    "diamond_jw_w_max": 0.82,
    "diamond_fw_jw_close": 0.025,   # forehead ~ jaw
    "heart_fw_jw_min": 1.15,        # client: FW/JW > 1.15
    "triangle_fw_jw_max": 0.85,     # client: FW/JW < 0.85
    "square_jw_w_min": 0.82,        # strong jaw
    "square_fw_jw_max": 1.05,       # minimal taper (JW/FW 0.85-1.0 band)
    "square_jaw_angle_max": 132.0,  # angular gonial angle (degrees)
}


def _d(lm, a, b):
    return float(np.linalg.norm(lm[a, :2] - lm[b, :2]))


def _angle(lm, a, b, c):
    v1 = lm[a, :2] - lm[b, :2]
    v2 = lm[c, :2] - lm[b, :2]
    cosv = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cosv, -1, 1))))


def face_metrics(lm) -> dict:
    H = _d(lm, 10, 152)
    W = _d(lm, 234, 454)
    FW = _d(lm, 54, 284)
    JW = _d(lm, 172, 397)
    lower_jaw = _d(lm, 150, 379)
    c = CALIBRATION
    fw_jw_mesh = FW / JW
    return {
        "face_height_to_width": round(H / W * c["height_factor"], 3),
        "forehead_to_jaw": round(c["fw_jw_centre_true"] + (fw_jw_mesh - c["fw_jw_centre_mesh"]) * c["fw_jw_gain"], 3),
        "forehead_to_cheek": round(FW / W, 3),
        "jaw_to_cheek": round(JW / W, 3),
        "jaw_curve": round(lower_jaw / JW, 3),
        "jaw_angle_deg": round(0.5 * (_angle(lm, 234, 172, 152) + _angle(lm, 454, 397, 152)), 1),
        "raw": {"H": round(H, 1), "W": round(W, 1), "FW": round(FW, 1), "JW": round(JW, 1),
                "fw_jw_mesh": round(fw_jw_mesh, 3)},
    }


def classify_face_shape(m: dict):
    """Returns (face_shape_id, rule_trace). Order is the client's."""
    r = RULES
    hw, fj = m["face_height_to_width"], m["forehead_to_jaw"]
    trace = []

    def rule(name, ok, why):
        trace.append({"shape": name, "fired": bool(ok), "test": why})
        return ok

    if rule("oblong", hw > r["oblong_hw_min"], f"H:W {hw} > {r['oblong_hw_min']}"):
        return "oblong", trace
    if rule("round", hw <= r["round_hw_max"] and m["jaw_curve"] >= r["round_jaw_curve_min"],
            f"H:W {hw} <= {r['round_hw_max']} and jaw curve {m['jaw_curve']} >= {r['round_jaw_curve_min']}"):
        return "round", trace
    if rule("diamond", m["forehead_to_cheek"] <= r["diamond_fw_w_max"] and m["jaw_to_cheek"] <= r["diamond_jw_w_max"]
            and abs(m["forehead_to_cheek"] - m["jaw_to_cheek"]) <= r["diamond_fw_jw_close"],
            f"cheekbones widest: FW/W {m['forehead_to_cheek']}, JW/W {m['jaw_to_cheek']}"):
        return "diamond", trace
    if rule("heart", fj > r["heart_fw_jw_min"], f"FW/JW {fj} > {r['heart_fw_jw_min']}"):
        return "heart", trace
    if rule("triangle", fj < r["triangle_fw_jw_max"], f"FW/JW {fj} < {r['triangle_fw_jw_max']}"):
        return "triangle", trace
    if rule("square", m["jaw_to_cheek"] >= r["square_jw_w_min"] and fj <= r["square_fw_jw_max"]
            and m["jaw_angle_deg"] <= r["square_jaw_angle_max"],
            f"JW/W {m['jaw_to_cheek']} >= {r['square_jw_w_min']}, FW/JW {fj} <= {r['square_fw_jw_max']}, "
            f"jaw angle {m['jaw_angle_deg']} <= {r['square_jaw_angle_max']}"):
        return "square", trace
    rule("oval", True, "no strong classifier fired (client default)")
    return "oval", trace


# ------------------------------------------------------------- quality

def _luma(img):
    return 0.114 * img[..., 0] + 0.587 * img[..., 1] + 0.299 * img[..., 2]


def check_quality(image, faces):
    """Raise the error that routes to screen 26 or 84 when the photo fails."""
    if not faces:
        raise ApiError("NO_FACE", "We need your full face in frame for an accurate reading.", 422)
    h, w = image.shape[:2]
    if len(faces) > 1:
        sizes = sorted((_d(f, 234, 454) for f in faces), reverse=True)
        if sizes[1] > 0.6 * sizes[0]:
            raise ApiError("MULTIPLE_FACES", "Only one face should be in frame.", 422)
    lm = max(faces, key=lambda f: _d(f, 234, 454))
    W = _d(lm, 234, 454)
    if W < 0.18 * w or W < 160:
        raise ApiError("FACE_TOO_SMALL", "Move a little closer so your face fills the frame.", 422)
    nose = lm[1, :2]
    if not (0.15 * w < nose[0] < 0.85 * w and 0.12 * h < nose[1] < 0.88 * h):
        raise ApiError("FACE_NOT_CENTRED", "Face centred and fully visible.", 422)
    xs, ys = lm[:, 0], lm[:, 1]
    if xs.min() < -0.02 * w or xs.max() > 1.02 * w or ys.min() < -0.02 * h or ys.max() > 1.02 * h:
        raise ApiError("FACE_NOT_CENTRED", "Face centred and fully visible.", 422)
    yaw = (_d(lm, 1, 234) - _d(lm, 1, 454)) / W
    if abs(yaw) > 0.28:
        raise ApiError("FACE_TURNED", "Look straight at the camera.", 422)
    x0, y0 = int(max(0, xs.min())), int(max(0, ys.min()))
    x1, y1 = int(min(w, xs.max())), int(min(h, ys.max()))
    face = image[y0:y1, x0:x1].astype(np.float32)
    lum = float(np.median(_luma(face)))
    if lum < 50:
        raise ApiError("LOW_LIGHT", "The light is too low for an accurate reading.", 422,
                       {"face_luminance": round(lum, 1)})
    return lm, {"yaw": round(float(yaw), 3), "face_luminance": round(lum, 1),
                "face_width_px": round(W, 1)}


# ------------------------------------------------------------- skin tone

CHEEKS = {"right": [117, 118, 101, 50, 205, 187, 123], "left": [346, 347, 330, 280, 425, 411, 352]}


def _lab(bgr):
    px = np.uint8([[np.clip(bgr, 0, 255)]])
    L, a, b = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)[0, 0].astype(float)
    return L * 100 / 255, a - 128, b - 128


def detect_skin_tone(image, lm) -> dict:
    samples = []
    for side, idx in CHEEKS.items():
        poly = np.round(lm[idx, :2]).astype(np.int32)
        mask = np.zeros(image.shape[:2], np.uint8)
        cv2.fillConvexPoly(mask, cv2.convexHull(poly), 1)
        px = image[mask > 0].astype(np.float32)
        if len(px) > 20:
            lum = _luma(px)
            lo, hi = np.percentile(lum, [20, 90])
            samples.append(px[(lum >= lo) & (lum <= hi)])
    if not samples:
        return {"tone": "medium", "undertone": "neutral", "confidence": "low"}
    med = np.median(np.concatenate(samples), axis=0)
    L, a, b = _lab(med)
    # Individual Typology Angle (dermatology standard), banded onto the six
    # ARCH tones. Photo exposure still moves it, so this is only a
    # suggestion: the tone she picks on screen 14 always wins.
    ita = float(np.degrees(np.arctan2(L - 50.0, b)))
    bands = [(55, "fair"), (41, "light"), (28, "medium"), (10, "tan"), (-30, "deep")]
    tone = next((t for th, t in bands if ita > th), "rich")
    diff = b - a
    undertone = "warm" if diff > 6 else ("cool" if diff < 1 else "neutral")
    return {"tone": tone, "undertone": undertone, "ita_deg": round(ita, 1),
            "lab": [round(float(L), 1), round(float(a), 1), round(float(b), 1)],
            "hex": "#%02X%02X%02X" % (int(med[2]), int(med[1]), int(med[0])), "confidence": "suggestion"}


def nearest_palette_colour(bgr) -> str:
    L, a, b = _lab(bgr)
    best, bd = None, 1e9
    for c in COLOURS:
        h = c["hex"].lstrip("#")
        cb = (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))
        L2, a2, b2 = _lab(cb)
        d = (L - L2) ** 2 + 0.6 * ((a - a2) ** 2 + (b - b2) ** 2)
        if d < bd:
            best, bd = c["id"], d
    return best
