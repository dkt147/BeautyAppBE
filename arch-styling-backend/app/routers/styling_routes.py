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
from app.core.auth import User, can, current_user, require
from app.core.devtools import IS_DEV
from app.core.errors import ApiError
from app.routers.profile_routes import _date, has_face_scan_consent
from app.services import looks_service as LS
from app.services import render_service as RS
from app.services.profile_service import (effective_mode, get_profile, remember_finish, remember_mode,
                                          update_profile)
from app.services.scan_service import create_scan, get_scan, public_scan, recommendation_for

router = APIRouter()

Style = Literal["arch", "structured", "feathered", "bold", "straight", "micro", "sharp", "rounded"]
Intensity = Literal["understated", "defined", "deliberate"]
Mode = Literal["refine", "reshape"]
Finish = Literal["full", "ombre"]
Colour = Literal["blonde", "light_taupe", "taupe", "light_brown", "medium_brown", "chestnut", "dark_brown", "soft_black"]


# ===================================================================== SCAN

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/pjpeg", "application/octet-stream", None, ""}


async def _read_upload(photo: UploadFile) -> bytes:
    """F10: JPEG or PNG only, size cap (ARCH_MAX_UPLOAD_MB, 8 MB). EXIF is
    dropped because the photo is re-encoded before it is stored."""
    if (photo.content_type or "").lower() not in ALLOWED_TYPES:
        raise ApiError("UNSUPPORTED_IMAGE_TYPE", "Send the photo as a JPEG or PNG.", 415)
    limit = int(config.MAX_UPLOAD_MB * 1024 * 1024)
    data = await photo.read(limit + 1)
    if len(data) > limit:
        raise ApiError("IMAGE_TOO_LARGE", f"The photo is larger than {config.MAX_UPLOAD_MB:g} MB.", 413)
    is_jpeg = data[:3] == b"\xff\xd8\xff"
    is_png = data[:8] == b"\x89PNG\r\n\x1a\n"
    if not (is_jpeg or is_png):
        raise ApiError("BAD_IMAGE", "The photo could not be read. Send a JPEG or PNG.", 400)
    return data


def _scan_out(doc: dict) -> dict:
    """One scan shape for POST /v1/scans, GET /v1/scans/latest and
    GET /v1/scans/{id}: all carry before_images (QA report item 8)."""
    out = public_scan(doc)
    out["before_images"] = RS.before_images(doc)
    return out


@router.post("/v1/scans", status_code=201, tags=["Scan 25-28"],
             summary="25 Scanning: upload one face photo -> face shape, brow reading, recommendation (27, 28)")
async def scan(photo: UploadFile = File(..., description="Front-facing photo (JPEG / PNG)"),
               face_shape_override: Optional[str] = Form(None, include_in_schema=IS_DEV,
                                                         description="Dev only: force a face shape"),
               user: User = Depends(current_user)):
    require(user, "scan", gate="13")
    if not has_face_scan_consent(user):
        raise ApiError("CONSENT_REQUIRED", "Face scan consent is needed first (screen 23).", 403)
    data = await _read_upload(photo)
    if face_shape_override and not IS_DEV:
        face_shape_override = None                      # M0: test field ignored outside dev
    doc = create_scan(user, data, face_shape_override or None, get_profile(user.id))
    update_profile(user.id, face_shape=doc["face_shape"]["id"], last_scan_id=doc["id"], last_scan_at=doc["created_at"])
    out = _scan_out(doc)
    out["next_screen"] = "27"
    return out


@router.get("/v1/scans/latest", tags=["Scan 25-28"], summary="Her most recent scan")
def latest_scan(user: User = Depends(current_user)):
    require(user, "scan", gate="13")
    rows = db.list_for_user("scans", user.id, limit=1)
    if not rows:
        raise ApiError("SCAN_NOT_FOUND", "No scan yet. Start a new scan.", 404)
    return _scan_out(rows[0])


@router.get("/v1/scans/{scan_id}", tags=["Scan 25-28"], summary="27 Scan Complete / 28 Post-Scan Discovery data")
def read_scan(scan_id: str, user: User = Depends(current_user)):
    require(user, "scan", gate="13")
    return _scan_out(get_scan(user, scan_id))


# ================================================================ CATALOGUE

def _style_card(sid, rec=None):
    M = load_measurements()
    st = M.style(sid)
    face = rec["face_shape"] if rec else None
    card = {
        "id": sid, "name": st.name, "label": st.name.upper(), "reading": C.STYLE_READINGS[sid],
        "grid_position": C.STYLE_ORDER.index(sid) + 1,
        "diagram_url": f"{config.PUBLIC_BASE_URL}/v1/styles/{sid}/diagram.png" + (f"?face_shape={face}" if face else ""),
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
    remembered = None if user.is_guest else get_profile(user.id).get("finish")
    return {"measurement_version": M.version, "legend": "Recommended for you",
            # 29: the Full / Ombre control returns with her last finish (null = never chosen; show FULL).
            "remembered_finish": remembered, "base_finish": C.BASE_FINISH,
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
    return {"default": best,
            "colours": [{**c, "best_for_you": c["id"] == best, "closest_to_your_brows": c["id"] == natural}
                        for c in C.COLOURS]}


@router.get("/v1/intensities", tags=["Catalogue 29"], summary="31 Intensity Selector copy")
def intensities():
    return {"title": "How far would you like to take it?", "line": "The same shape, three expressions.",
            "intensities": [{"id": k, **C.INTENSITIES[k]} for k in C.INTENSITY_ORDER],
            "cta": "SEE THIS LOOK", "compare": "Compare two intensities"}


@router.get("/v1/modes", tags=["Catalogue 29"], summary="30 toggle + 30a mode introduction copy")
def modes(user: User = Depends(current_user)):
    p = None if user.is_guest else get_profile(user.id)
    return {"current": effective_mode(p) if p else None,
            "remembered": p.get("mode") if p else None, "starting_mode": C.STARTING_MODE,
            "modes": C.MODES, "intro_30a": C.MODE_INTRO}


@router.get("/v1/face-shapes", tags=["Catalogue 29"], summary="Face shape table from the Measurement JSON")
def face_shapes():
    M = load_measurements()
    return {"version": M.version, "face_shapes": [
        {**fs.__dict__, "tagline": C.FACE_SHAPE_TAGLINES[fid]} for fid, fs in M.face_shapes.items()]}


# =================================================================== TRY-ON

class TryOnIn(BaseModel):
    scan_id: str
    style: Style
    colour: Optional[Colour] = Field(None, description="Swatch on 29. Empty = her brow profile, then her scan.")
    intensity: Optional[Intensity] = Field(None, description="31 to 34. Empty = her style direction's intensity.")
    mode: Optional[Mode] = Field(None, description="REFINE MINE / RESHAPE MINE. Sending it remembers it for her "
                                                  "account. Empty = the remembered mode.")
    finish: Finish = Field(..., description="Required. full or ombre. Straight and Micro: full only (ombre is a 422).")
    views: List[Literal["full", "face", "brow", "eyes"]] = Field(default_factory=lambda: ["face", "brow", "eyes", "full"])


def _resolve(user, scan, body, need_intensity=True):
    """Fill colour, intensity and mode only from values somebody set (Spec
    Rule 2): the request, then her brow profile, then her scan's
    recommendation. Returns the values and where each came from. A mode sent
    in the request is remembered for her account (build plan M3)."""
    p = get_profile(user.id)
    rec = scan["recommendation"]
    sent = body.model_dump()
    out, src = {}, {}
    if sent.get("colour"):
        out["colour"], src["colour"] = sent["colour"], "request"
    elif p.get("preferred_colour"):
        out["colour"], src["colour"] = p["preferred_colour"], "brow_profile"
    else:
        out["colour"], src["colour"] = rec["colour"]["id"], "scan_recommendation"
    if sent.get("mode"):
        out["mode"], src["mode"] = sent["mode"], "request"
        remember_mode(user.id, sent["mode"])
    else:
        out["mode"] = effective_mode(p)
        src["mode"] = "remembered" if p.get("mode") else (
            "style_direction" if p.get("style_direction") else "starting_mode")
    # Finish is required on every try-on and save (final client changes).
    out["finish"], src["finish"] = sent["finish"], "request"
    RS.check_finish(body.style, out["finish"])
    remember_finish(user.id, body.style, out["finish"])
    if need_intensity:
        if sent.get("intensity"):
            out["intensity"], src["intensity"] = sent["intensity"], "request"
        elif rec.get("intensity"):
            out["intensity"], src["intensity"] = rec["intensity"], "style_direction"
        else:
            raise ApiError("INTENSITY_REQUIRED",
                           "Choose an intensity: understated, defined or deliberate.", 422)
    return out, src


def _first_visit_30a(user):
    return not user.doc.get("flags", {}).get("mode_intro_seen", False)


@router.post("/v1/tryon/render", tags=["Try-on 29-36"],
             summary="29 preview / 30 Style Applied / 32-34 intensity / 36 your look: render one look on her photo")
def tryon_render(body: TryOnIn, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    sc = get_scan(user, body.scan_id)
    v, src = _resolve(user, sc, body)
    t0 = time.time()
    r = RS.render(user, sc, body.style, v["colour"], v["intensity"], v["mode"], body.views, finish=v["finish"])
    return {**body.model_dump(), **v, "resolved_from": src, **r,
            "copy": RS.look_copy(body.style, v["colour"], v["intensity"], v["mode"], v["finish"]),
            "face_shape": sc["face_shape"]["id"],
            "is_recommended": body.style in (sc["recommendation"]["recommended"]["style"],
                                             sc["recommendation"]["alternate"]["style"]),
            "show_mode_intro_30a": _first_visit_30a(user),
            "render_ms": int((time.time() - t0) * 1000)}


class IntensitiesIn(BaseModel):
    scan_id: str
    style: Style
    colour: Optional[Colour] = None
    mode: Optional[Mode] = None
    finish: Finish = Field(..., description="Required. full or ombre. Straight and Micro: full only (ombre is a 422).")


@router.post("/v1/tryon/intensities", tags=["Try-on 29-36"],
             summary="31 Intensity Selector: the same shape in all three intensities (eye-strip thumbnails)")
def tryon_intensities(body: IntensitiesIn, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    sc = get_scan(user, body.scan_id)
    v, src = _resolve(user, sc, body, need_intensity=False)
    items = []
    for it in C.INTENSITY_ORDER:
        r = RS.render(user, sc, body.style, v["colour"], it, v["mode"], ["eyes", "face"], finish=v["finish"])
        items.append({"intensity": it, "name": C.INTENSITIES[it]["name"],
                      "lines": C.INTENSITIES[it]["selector_lines"], **r,
                      "next_screen": {"understated": "32", "defined": "33", "deliberate": "34"}[it]})
    return {"title": "How far would you like to take it?", "line": "The same shape, three expressions.",
            **v, "resolved_from": src, "items": items}


class CompareIn(BaseModel):
    scan_id: str
    style: Style
    colour: Optional[Colour] = None
    mode: Optional[Mode] = None
    finish: Finish = Field(..., description="Required. full or ombre. Straight and Micro: full only (ombre is a 422).")
    intensities: List[Intensity] = Field(..., min_length=2, max_length=2, description="The two chosen on 35a")


@router.post("/v1/tryon/compare", tags=["Try-on 29-36"], summary="35b Two Looks: two intensities side by side")
def tryon_compare(body: CompareIn, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    if body.intensities[0] == body.intensities[1]:
        raise ApiError("VALIDATION_ERROR", "Choose two different intensities.", 422)
    sc = get_scan(user, body.scan_id)
    v, src = _resolve(user, sc, body, need_intensity=False)
    looks = []
    for it in body.intensities:
        r = RS.render(user, sc, body.style, v["colour"], it, v["mode"], ["face", "eyes"], finish=v["finish"])
        looks.append({"intensity": it, "name": C.INTENSITIES[it]["name"], **r,
                      "cta": f"I CHOOSE {C.INTENSITIES[it]['name'].upper()}"})
    return {"title": "Two looks. One choice.", "line": "Take your time with it.", **v, "resolved_from": src,
            "looks": looks, "alt": "Go back to all styles"}


@router.get("/v1/tryon/before", tags=["Try-on 29-36"], summary="Her photo without a brow style, same crops")
def tryon_before(scan_id: str, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    return {"images": RS.before_images(get_scan(user, scan_id))}


class BeforeAfterIn(BaseModel):
    scan_id: str
    style: Style
    colour: Optional[Colour] = None
    intensity: Optional[Intensity] = None
    mode: Optional[Mode] = None
    finish: Finish = Field(..., description="Required. full or ombre. Straight and Micro: full only (ombre is a 422).")
    views: List[Literal["full", "face", "brow", "eyes"]] = Field(default_factory=lambda: ["eyes", "face"])


@router.post("/v1/tryon/before-after", tags=["Try-on 29-36"],
             summary="44 The Difference: BEFORE and AFTER panels from the same photo")
def tryon_before_after(body: BeforeAfterIn, user: User = Depends(current_user)):
    require(user, "tryon", gate="13")
    sc = get_scan(user, body.scan_id)
    v, src = _resolve(user, sc, body)
    before = RS.before_images(sc)
    after = RS.render(user, sc, body.style, v["colour"], v["intensity"], v["mode"], body.views, finish=v["finish"])
    style_name = load_measurements().style(body.style).name
    return {**v, "style": body.style, "resolved_from": src,
            "before": {"label": "BEFORE", "line": "Where you’re beginning. Already beautiful.",
                       "images": {k: before[k] for k in body.views}},
            "after": {"label": "AFTER", "line": f"After: {style_name}", "render_id": after["render_id"],
                      "images": after["images"]},
            "screen_44": {"title": "The difference, clearly shown.", "cta": "THIS IS THE ONE", "cta_to": "30",
                          "alt": "Try another style", "alt_to": "29"}}


# ==================================================================== LOOKS

class LookIn(BaseModel):
    scan_id: str
    style: Style
    colour: Optional[Colour] = None
    intensity: Optional[Intensity] = None
    mode: Optional[Mode] = None
    finish: Finish = Field(..., description="Required. full or ombre. Straight and Micro: full only (ombre is a 422).")
    name: Optional[str] = Field(None, max_length=60, description="LOOK NAME on 37; default 'Structured · Defined · Dark "
                                                               "Brown', plus ' · Ombre' in Ombre. No tag (spec 3.2)")


@router.post("/v1/looks", status_code=201, tags=["Looks 37-38"], summary="37 SAVE THIS LOOK -> 38 Saved Confirmation")
def save_look(body: LookIn, user: User = Depends(current_user)):
    require(user, "save_look", gate="13a")
    sc = get_scan(user, body.scan_id)
    sel, _ = _resolve(user, sc, body)
    doc, copy = LS.create_look(user, sc, body.style, sel["colour"], sel["intensity"], sel["mode"],
                               sel["finish"], body.name)
    doc = LS.decorate(doc)
    update_profile(user.id, preferred_style=body.style, preferred_colour=sel["colour"])
    return {"look": doc, "screen_38": {
        "title": "Saved.", "editorial_title": copy["editorial_title"], "caption": copy["caption"],
        "line": "This look is in My Looks — ready whenever you need it.", "mode_label": copy["mode_label"],
        "cta": "VIEW MY LOOKS", "alt": "Return to home"}}


@router.get("/v1/looks", tags=["Looks 37-38"],
            summary="50 / 51 My Looks, newest first. tab = all | traced | previewed (feeds 21 too)")
def list_looks(tab: Literal["all", "traced", "previewed"] = Query("all"), user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    looks = LS.list_for(user.id, tab)
    member = can(user, "save_look")
    out = {"tab": tab, "looks": looks, "screen": "50" if looks or tab != "all" else "51",
           "is_member": member, "create_new_to": "29" if get_profile(user.id).get("last_scan_id") else "22"}
    if not member:            # 51 free account: "See what membership includes" -> 64
        out["membership_line"] = {"text": "See what membership includes", "to": "64"}
    return out


@router.get("/v1/looks/{look_id}", tags=["Looks 37-38"], summary="One look (36 when opened / RE-APPLY)")
def get_look(look_id: str, user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    lk = db.get("looks", look_id)
    if not lk or lk["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Look not found.", 404)
    copy = RS.look_copy(lk["style"], lk["colour"], lk["intensity"], lk["mode"], lk.get("finish") or "full") \
        if lk.get("style") else None
    return {"look": LS.decorate(lk), "copy": copy}


@router.delete("/v1/looks/{look_id}", tags=["Looks 37-38"], summary="Delete a look")
def delete_look(look_id: str, user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    lk = db.get("looks", look_id)
    if not lk or lk["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Look not found.", 404)
    db.delete("looks", look_id)
    shutil.rmtree(config.MEDIA_DIR / "looks" / look_id, ignore_errors=True)
    if lk.get("guide_id"):                      # a saved guide's look: remove the guide too
        shutil.rmtree(config.MEDIA_DIR / "guides" / lk["guide_id"], ignore_errors=True)
        db.delete("guides", lk["guide_id"])
    return {"deleted": look_id}
