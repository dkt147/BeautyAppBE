"""Screens 25 to 38: scan, catalogue, try-on (style, mode, intensity,
compare) and saving a look."""
import shutil
import time
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core import db
from app.core.auth import User, current_user, require
from app.core.errors import ApiError
from app.routers.profile_routes import _date, has_face_scan_consent
from app.services import render_service as RS
from app.services.profile_service import get_profile, update_profile
from app.services.scan_service import create_scan, get_scan, public_scan, recommendation_for

router = APIRouter()

Style = Literal["arch", "structured", "feathered", "bold", "straight", "micro", "sharp", "rounded"]
Intensity = Literal["understated", "defined", "deliberate"]
Mode = Literal["refine", "reshape"]
Colour = Literal["blonde", "light_taupe", "taupe", "light_brown", "medium_brown", "chestnut", "dark_brown", "soft_black"]


# ===================================================================== SCAN

@router.post("/v1/scans", status_code=201, tags=["Scan 25-28"],
             summary="25 Scanning: upload one face photo -> face shape, brow reading, recommendation (27, 28)")
async def scan(photo: UploadFile = File(..., description="Front-facing photo (JPEG / PNG)"),
               face_shape_override: Optional[str] = Form(None, description="Testing only: force a face shape"),
               user: User = Depends(current_user)):
    require(user, "scan", gate="13")
    if not has_face_scan_consent(user):
        raise ApiError("CONSENT_REQUIRED", "Face scan consent is needed first (screen 23).", 403)
    data = await photo.read()
    doc = create_scan(user, data, face_shape_override or None, get_profile(user.id))
    update_profile(user.id, face_shape=doc["face_shape"]["id"], last_scan_id=doc["id"], last_scan_at=doc["created_at"])
    out = public_scan(doc)
    out["before_images"] = RS.before_images(doc)
    out["next_screen"] = "27"
    return out


@router.get("/v1/scans/latest", tags=["Scan 25-28"], summary="Her most recent scan")
def latest_scan(user: User = Depends(current_user)):
    require(user, "scan", gate="13")
    rows = db.list_for_user("scans", user.id, limit=1)
    if not rows:
        raise ApiError("SCAN_NOT_FOUND", "No scan yet. Start a new scan.", 404)
    return public_scan(rows[0])


@router.get("/v1/scans/{scan_id}", tags=["Scan 25-28"], summary="27 Scan Complete / 28 Post-Scan Discovery data")
def read_scan(scan_id: str, user: User = Depends(current_user)):
    require(user, "scan", gate="13")
    return public_scan(get_scan(user, scan_id))


# ================================================================ CATALOGUE

def _style_card(sid, rec=None):
    M = load_measurements()
    st = M.style(sid)
    face = rec["face_shape"] if rec else None
    card = {
        "id": sid, "name": st.name, "label": st.name.upper(), "reading": C.STYLE_READINGS[sid],
        "grid_position": C.STYLE_ORDER.index(sid) + 1,
        "diagram_url": f"/v1/styles/{sid}/diagram.png" + (f"?face_shape={face}" if face else ""),
        "measurements": {"length_ew": st.length_ew, "peak_type": st.peak_type,
                         "peak_position_pct": M.peak_pct(sid, face), "plateau_range_pct": M.plateau(sid, face),
                         "peak_height_ew": st.peak_height_ew, "thickness_head_ew": st.thickness_head_ew,
                         "thickness_body_ew": st.thickness_body_ew, "thickness_tail_ew": st.thickness_tail_ew,
                         "tail_vs_head_offset_ew": st.tail_offset_ew},
        "recommended_for_you": False, "role": None, "avoid_for_face": False,
    }
    if rec:
        if sid == rec["recommended"]["style"]:
            card.update(recommended_for_you=True, role="recommended")
        elif sid == rec["alternate"]["style"]:
            card.update(recommended_for_you=True, role="alternate")
        card["avoid_for_face"] = sid in rec["avoid"]
    return card


@router.get("/v1/styles", tags=["Catalogue 29"], summary="29 STYLE grid: eight styles, with her recommended dots")
def styles(scan_id: Optional[str] = Query(None, description="Adds 'Recommended for you' from this scan"),
           user: User = Depends(current_user)):
    rec = None
    if scan_id:
        require(user, "scan", gate="13")
        rec = get_scan(user, scan_id)["recommendation"]
    M = load_measurements()
    return {"measurement_version": M.version, "legend": "Recommended for you",
            "styles": [_style_card(s, rec) for s in C.STYLE_ORDER]}


@router.get("/v1/styles/{style_id}", tags=["Catalogue 29"], summary="One style with its 3 editorial titles")
def style(style_id: Style, user: User = Depends(current_user)):
    card = _style_card(style_id)
    card["editorial_titles"] = C.EDITORIAL_TITLES[style_id]
    card["style_applied_copy"] = C.STYLE_APPLIED_COPY[style_id]
    return card


@router.get("/v1/colours", tags=["Catalogue 29"], summary="29 COLOUR row (8 swatches), best shade flagged")
def colours(scan_id: Optional[str] = None, user: User = Depends(current_user)):
    best = None
    natural = None
    if scan_id:
        require(user, "scan", gate="13")
        sc = get_scan(user, scan_id)
        best = sc["recommendation"]["colour"]["id"]
        natural = sc["natural_brow_colour"]["id"]
    elif not user.is_guest:
        best = get_profile(user.id).get("preferred_colour")
    return {"default": best or C.DEFAULT_COLOUR,
            "colours": [{**c, "best_for_you": c["id"] == best, "closest_to_your_brows": c["id"] == natural}
                        for c in C.COLOURS]}


@router.get("/v1/intensities", tags=["Catalogue 29"], summary="31 Intensity Selector copy")
def intensities():
    return {"title": "How far would you like to take it?", "line": "The same shape, three expressions.",
            "intensities": [{"id": k, **C.INTENSITIES[k]} for k in C.INTENSITY_ORDER],
            "cta": "SEE THIS LOOK", "compare": "Compare two intensities"}


@router.get("/v1/modes", tags=["Catalogue 29"], summary="30 toggle + 30a mode introduction copy")
def modes():
    return {"default": C.DEFAULT_MODE, "modes": C.MODES, "intro_30a": C.MODE_INTRO}


@router.get("/v1/face-shapes", tags=["Catalogue 29"], summary="Face shape table from the Measurement JSON")
def face_shapes():
    M = load_measurements()
    return {"version": M.version, "face_shapes": [
        {**fs.__dict__, "tagline": C.FACE_SHAPE_TAGLINES[fid]} for fid, fs in M.face_shapes.items()]}


# =================================================================== TRY-ON

class TryOnIn(BaseModel):
    scan_id: str
    style: Style
    colour: Colour = "dark_brown"
    intensity: Intensity = "defined"
    mode: Mode = "reshape"
    views: List[Literal["full", "face", "brow", "eyes"]] = Field(default_factory=lambda: ["face", "brow", "eyes", "full"])


def _first_visit_30a(user):
    return not user.doc.get("flags", {}).get("mode_intro_seen", False)


@router.post("/v1/tryon/render", tags=["Try-on 29-36"],
             summary="29 preview / 30 Style Applied / 32-34 intensity / 36 your look: render one look on her photo")
def tryon_render(body: TryOnIn, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    sc = get_scan(user, body.scan_id)
    t0 = time.time()
    r = RS.render(user, sc, body.style, body.colour, body.intensity, body.mode, body.views)
    return {**body.model_dump(), **r, "copy": RS.look_copy(body.style, body.colour, body.intensity, body.mode),
            "face_shape": sc["face_shape"]["id"],
            "is_recommended": body.style in (sc["recommendation"]["recommended"]["style"],
                                             sc["recommendation"]["alternate"]["style"]),
            "show_mode_intro_30a": _first_visit_30a(user),
            "render_ms": int((time.time() - t0) * 1000)}


class IntensitiesIn(BaseModel):
    scan_id: str
    style: Style
    colour: Colour = "dark_brown"
    mode: Mode = "reshape"


@router.post("/v1/tryon/intensities", tags=["Try-on 29-36"],
             summary="31 Intensity Selector: the same shape in all three intensities (eye-strip thumbnails)")
def tryon_intensities(body: IntensitiesIn, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    sc = get_scan(user, body.scan_id)
    items = []
    for it in C.INTENSITY_ORDER:
        r = RS.render(user, sc, body.style, body.colour, it, body.mode, ["eyes", "face"])
        items.append({"intensity": it, "name": C.INTENSITIES[it]["name"],
                      "lines": C.INTENSITIES[it]["selector_lines"], **r,
                      "next_screen": {"understated": "32", "defined": "33", "deliberate": "34"}[it]})
    return {"title": "How far would you like to take it?", "line": "The same shape, three expressions.",
            "items": items}


class CompareIn(BaseModel):
    scan_id: str
    style: Style
    colour: Colour = "dark_brown"
    mode: Mode = "reshape"
    intensities: List[Intensity] = Field(..., min_length=2, max_length=2, description="The two chosen on 35a")


@router.post("/v1/tryon/compare", tags=["Try-on 29-36"], summary="35b Two Looks: two intensities side by side")
def tryon_compare(body: CompareIn, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    if body.intensities[0] == body.intensities[1]:
        raise ApiError("VALIDATION_ERROR", "Choose two different intensities.", 422)
    sc = get_scan(user, body.scan_id)
    looks = []
    for it in body.intensities:
        r = RS.render(user, sc, body.style, body.colour, it, body.mode, ["face", "eyes"])
        looks.append({"intensity": it, "name": C.INTENSITIES[it]["name"], **r,
                      "cta": f"I CHOOSE {C.INTENSITIES[it]['name'].upper()}"})
    return {"title": "Two looks. One choice.", "line": "Take your time with it.", "mode": body.mode,
            "looks": looks, "alt": "Go back to all styles"}


@router.get("/v1/tryon/before", tags=["Try-on 29-36"], summary="Her photo without a brow style, same crops")
def tryon_before(scan_id: str, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    return {"images": RS.before_images(get_scan(user, scan_id))}


# ==================================================================== LOOKS

class LookIn(BaseModel):
    scan_id: str
    style: Style
    colour: Colour = "dark_brown"
    intensity: Intensity = "defined"
    mode: Mode = "reshape"
    name: Optional[str] = Field(None, max_length=60, description="LOOK NAME on 37; default 'Structured · Defined · Dark Brown'")
    tag: Optional[Literal["everyday", "occasion"]] = None


@router.post("/v1/looks", status_code=201, tags=["Looks 37-38"], summary="37 SAVE THIS LOOK -> 38 Saved Confirmation")
def save_look(body: LookIn, user: User = Depends(current_user)):
    require(user, "save_look", gate="13a")
    sc = get_scan(user, body.scan_id)
    r = RS.render(user, sc, body.style, body.colour, body.intensity, body.mode, ["full", "face", "eyes"])
    copy = RS.look_copy(body.style, body.colour, body.intensity, body.mode)
    look_id = db.new_id("look")
    ldir = config.MEDIA_DIR / "looks" / look_id
    ldir.mkdir(parents=True, exist_ok=True)
    images = {}
    for v, url in r["images"].items():
        src = config.MEDIA_DIR / url.split("/media/", 1)[1]
        shutil.copy(src, ldir / f"{v}.jpg")
        images[v] = config.media_url(f"looks/{look_id}/{v}.jpg")
    now = time.time()
    doc = {"id": look_id, "user_id": user.id, "created_at": now, "scan_id": sc["id"],
           "style": body.style, "colour": body.colour, "intensity": body.intensity, "mode": body.mode,
           "face_shape": sc["face_shape"]["id"],
           "name": (body.name or copy["caption"]).strip(), "tag": body.tag,
           "caption": copy["caption"], "editorial_title": copy["editorial_title"],
           "mode_label": copy["mode_label"], "images": images}
    db.put("looks", look_id, user.id, doc)
    update_profile(user.id, preferred_style=body.style, preferred_colour=body.colour)
    return {"look": doc, "screen_38": {
        "title": "Saved.", "editorial_title": copy["editorial_title"], "caption": copy["caption"],
        "line": "This look is in My Looks — ready whenever you need it.", "mode_label": copy["mode_label"],
        "cta": "VIEW MY LOOKS", "alt": "Return to home"}}


@router.get("/v1/looks", tags=["Looks 37-38"], summary="Saved looks, newest first (feeds 50 / 21)")
def list_looks(user: User = Depends(current_user)):
    require(user, "save_look", gate="13a")
    looks = db.list_for_user("looks", user.id)
    for lk in looks:
        lk["saved_label"] = f"{_date(lk['created_at'])} · {load_measurements().style(lk['style']).name} · {C.colour_label(lk['colour'])}"
    return {"looks": looks}


@router.get("/v1/looks/{look_id}", tags=["Looks 37-38"], summary="One look (36 when opened / RE-APPLY)")
def get_look(look_id: str, user: User = Depends(current_user)):
    require(user, "save_look", gate="13a")
    lk = db.get("looks", look_id)
    if not lk or lk["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Look not found.", 404)
    return {"look": lk, "copy": RS.look_copy(lk["style"], lk["colour"], lk["intensity"], lk["mode"])}


@router.delete("/v1/looks/{look_id}", tags=["Looks 37-38"], summary="Delete a look")
def delete_look(look_id: str, user: User = Depends(current_user)):
    require(user, "save_look", gate="13a")
    lk = db.get("looks", look_id)
    if not lk or lk["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Look not found.", 404)
    db.delete("looks", look_id)
    shutil.rmtree(config.MEDIA_DIR / "looks" / look_id, ignore_errors=True)
    return {"deleted": look_id}
