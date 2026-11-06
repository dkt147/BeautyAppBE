"""Try-on renders for screens 29 to 37, cached per (scan, style, colour,
intensity, mode). Views are crops of one full render:

  full   whole photo                      (save / share)
  face   portrait crop, 4:5               (screens 30, 32-34, 36, 37)
  brow   close-up of one brow             (screen 29 preview)
  eyes   eye-and-brow strip               (screen 31 thumbnails, 35a/35b)
"""
import hashlib
import zlib

import cv2
import numpy as np

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core.errors import ApiError
from app.rendering.brow_renderer import BrowRenderer
from app.services.scan_service import load_scan_assets, scan_dir

RENDERER = BrowRenderer()
VIEWS = ("full", "face", "brow", "eyes")


def validate(style, colour, intensity, mode, finish="full"):
    M = load_measurements()
    if style not in M.styles:
        raise ApiError("VALIDATION_ERROR", f"Unknown style '{style}'. Use one of: {', '.join(C.STYLE_ORDER)}", 422)
    if colour not in C.COLOUR_BY_ID:
        raise ApiError("VALIDATION_ERROR", f"Unknown colour '{colour}'. Use one of: {', '.join(C.COLOUR_BY_ID)}", 422)
    if intensity not in C.INTENSITIES:
        raise ApiError("VALIDATION_ERROR", f"Unknown intensity '{intensity}'.", 422)
    if mode not in C.MODES:
        raise ApiError("VALIDATION_ERROR", f"Unknown mode '{mode}'. Use refine or reshape.", 422)
    check_finish(style, finish)


def check_finish(style, finish):
    if finish not in C.FINISHES:
        raise ApiError("VALIDATION_ERROR", f"Unknown finish '{finish}'. Use full or ombre.", 422)
    if finish == "ombre" and not C.SUPPORTS_OMBRE.get(style, False):
        raise ApiError("FINISH_NOT_AVAILABLE",
                       f"{load_measurements().style(style).name} comes in the Full finish only.", 422)


def _crop(img, box):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    return img[y0:y1, x0:x1]


def _boxes(scan, lm):
    fx0, fy0, fx1, fy1 = scan["face_box"]
    fw, fh = fx1 - fx0, fy1 - fy0
    cx = 0.5 * (fx0 + fx1)
    # face: 4:5 portrait, forehead to chin with a little air
    bw = fw * 1.25
    bh = bw * 1.25
    top = fy0 - 0.12 * fh
    face = (cx - bw / 2, top, cx + bw / 2, top + bh)
    brows = lm[[70, 63, 105, 66, 107, 336, 296, 334, 293, 300], :2]
    eyes = lm[[33, 133, 362, 263, 159, 386, 145, 374], :2]
    ex0, ex1 = brows[:, 0].min(), brows[:, 0].max()
    ey0 = brows[:, 1].min()
    ey1 = eyes[:, 1].max()
    pad = 0.18 * (ex1 - ex0)
    eyes_box = (ex0 - pad, ey0 - 0.9 * pad, ex1 + pad, ey1 + 0.5 * pad)
    # one brow: the person's right brow (image left), wide crop like screen 29
    rb = lm[[70, 63, 105, 66, 107, 46, 53, 52, 65, 55, 33, 133], :2]
    bx0, bx1 = rb[:, 0].min(), rb[:, 0].max()
    by0, by1 = rb[:, 1].min(), rb[:, 1].max()
    bp = 0.22 * (bx1 - bx0)
    brow = (bx0 - bp, by0 - 1.1 * bp, bx1 + bp, by1 + 0.25 * bp)
    return {"face": face, "eyes": eyes_box, "brow": brow}


def render(user, scan, style, colour, intensity, mode, views=VIEWS, finish="full"):
    validate(style, colour, intensity, mode, finish)
    M = load_measurements()
    face_shape = scan["face_shape"]["id"]
    key = f"{style}|{colour}|{intensity}|{mode}|{face_shape}|{M.version}|r2"
    if finish != "full":                     # Full keeps its existing cache key
        key += f"|{finish}"
    h = hashlib.sha1(key.encode()).hexdigest()[:12]
    d = scan_dir(scan["id"]) / "renders"
    d.mkdir(exist_ok=True)
    full_path = d / f"{h}_full.jpg"
    image = lm = None
    if not full_path.exists():
        image, lm, naturals = load_scan_assets(scan)
        seed = zlib.crc32(f"{scan['id']}|{style}|{mode}".encode()) & 0xFFFF
        out, _ = RENDERER.render(image, lm, M.style(style), M.peak_pct(style, face_shape),
                                 M.plateau(style, face_shape), C.COLOUR_BY_ID[colour]["hex"],
                                 intensity, mode, seed=seed, naturals=naturals, finish=finish)
        cv2.imwrite(str(full_path), out, [cv2.IMWRITE_JPEG_QUALITY, 93])
    urls = {}
    for v in views:
        p = d / f"{h}_{v}.jpg"
        if v != "full" and not p.exists():
            if lm is None:
                lm = np.load(scan_dir(scan["id"]) / "landmarks.npy").astype(np.float64)
            full = cv2.imread(str(full_path))
            crop = _crop(full, _boxes(scan, lm)[v])
            cv2.imwrite(str(p), crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
        urls[v] = config.media_url(f"scans/{scan['id']}/renders/{p.name}")
    return {"render_id": h, "images": urls}


def before_images(scan):
    """The un-styled photo in the same crops (for before/after and 30a)."""
    d = scan_dir(scan["id"])
    lm = np.load(d / "landmarks.npy").astype(np.float64)
    img = cv2.imread(str(d / "photo.jpg"))
    urls = {"full": scan["image"]["url"]}
    for v, box in _boxes(scan, lm).items():
        p = d / f"before_{v}.jpg"
        if not p.exists():
            cv2.imwrite(str(p), _crop(img, box), [cv2.IMWRITE_JPEG_QUALITY, 92])
        urls[v] = config.media_url(f"scans/{scan['id']}/{p.name}")
    return urls


def look_copy(style, colour, intensity, mode, finish="full"):
    """Every string the try-on screens show for this selection."""
    M = load_measurements()
    st = M.style(style)
    it = C.INTENSITIES[intensity]
    applied = C.STYLE_APPLIED_COPY[style]
    return {
        "style_name": st.name,
        "colour_name": C.colour_label(colour),
        "intensity_name": it["name"],
        "mode_label": C.MODES[mode]["label"],
        "finish_name": C.FINISHES[finish]["name"],
        "caption": C.look_caption(style, intensity, colour),                 # 36, 37 default name
        "caption_upper": C.look_caption(style, intensity, colour, upper=True),  # 29 caption
        "style_header": f"{st.name.upper()} STYLE",                          # 30 header
        "style_applied": {"headline": applied["headline"], "body": applied["body"],
                          "meta": f"{st.name} brow · {C.colour_label(colour)}",
                          "provisional": applied["provisional"]},             # 30
        "intensity_screen": {"header": it["name"].upper(), "title": it["name"],
                             "tagline": it["tagline"], "body": it["body"][mode]},  # 32-34
        "editorial_title": C.EDITORIAL_TITLES[style][intensity],             # 36, 38
    }
