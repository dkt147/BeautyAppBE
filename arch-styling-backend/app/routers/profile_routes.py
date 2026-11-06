"""Screens 12-21 and 23: session, guest gates, onboarding (14-18), home
(19-21) and the face scan consent (23)."""
import time
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from app import config
from app.catalogue import content as C
from app.core import db
from app.core.auth import User, current_user, require, save_user
from app.core.errors import ApiError
from app.services import consent_service as CS
from app.services.profile_service import get_profile, update_profile
from app.services.scan_service import brow_shades

router = APIRouter()


def _date(ts):
    if not ts:
        return None
    dt = datetime.fromtimestamp(ts)
    return f"{dt.day} {dt:%B %Y}"   # "12 October 2026" (works on Windows too)


# ----------------------------------------------------------------- session

# GET / PATCH /v1/me live in auth_routes.py (M1).

class FlagsIn(BaseModel):
    mode_intro_seen: Optional[bool] = Field(None, description="Screen 30a shown once per account; set true on GOT IT.")


@router.post("/v1/me/flags", tags=["Profile flags"], summary="Set one-time flags (30a)")
def set_flags(body: FlagsIn, user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    flags = user.doc.setdefault("flags", {})
    for k, v in body.model_dump(exclude_none=True).items():
        flags[k] = v
    save_user(user)
    return {"flags": flags}


@router.post("/v1/dev/reset-test-user", tags=["Dev tools"], summary="Wipe the test user (fresh onboarding)")
def reset_test_user(user: User = Depends(current_user)):
    require(user, "account")
    for t in ("profiles", "consents", "looks", "scans"):
        for row in db.list_for_user(t, user.id):
            db.delete(t, row["id"] if "id" in row else user.id)
    db.delete("profiles", user.id)
    db.delete("users", user.id)
    return {"reset": user.id}


# -------------------------------------------------------------- onboarding

@router.get("/v1/onboarding/options", tags=["Onboarding 14-18"], summary="Everything screens 14 and 16 list")
def onboarding_options(user: User = Depends(current_user)):
    return {
        "screen_14": {"step": "STEP 1 OF 2", "title": "A few things about you.",
                      "greeting": f"Hello, {user.name}.",
                      "skin_tones": C.SKIN_TONES, "undertones": C.UNDERTONES, "brow_goals": C.BROW_GOALS},
        "screen_16": {"step": "STEP 2 OF 2", "title": "Where would you like to begin?",
                      "directions": [{"id": k, "name": C.STYLE_DIRECTIONS[k]["name"],
                                      "line": C.STYLE_DIRECTIONS[k]["line"]} for k in C.DIRECTION_ORDER]},
    }


class Step1In(BaseModel):
    skin_tone: Literal["fair", "light", "medium", "tan", "deep", "rich"]
    undertone: Literal["warm", "neutral", "cool"] = "warm"
    brow_goal: Literal["shape", "colour", "both"]


@router.put("/v1/onboarding/skin-tone-goal", tags=["Onboarding 14-18"],
            summary="14 NEXT: save skin tone + goal, returns screen 15 (brow shades)")
def step1(body: Step1In, user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    update_profile(user.id, skin_tone=body.skin_tone, undertone=body.undertone,
                   brow_goal=body.brow_goal, skin_tone_confirmed=False)
    return _screen15(body.skin_tone, body.undertone)


def _screen15(tone, undertone):
    shades = brow_shades(tone, undertone)
    t = C.SKIN_TONE_BY_ID[tone]
    return {"screen_15": {
        "tone": {**t, "label": f"{t['name']} {undertone}"},
        "selected_line": f"{t['name']} {undertone} undertone · selected",
        "brow_shades": [{"role": "Best", **C.COLOUR_BY_ID[shades["best"]]}] +
                       [{"role": "Close", **C.COLOUR_BY_ID[c]} for c in shades["close"]],
        "line": "Chosen to complement your tone.",
        "provisional_mapping": True,
    }}


class ConfirmToneIn(BaseModel):
    preferred_colour: Optional[str] = Field(None, description="Shade she taps on 15 (defaults to Best).")


@router.post("/v1/onboarding/confirm-tone", tags=["Onboarding 14-18"], summary="15 CONFIRM THIS TONE")
def confirm_tone(body: ConfirmToneIn, user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    p = get_profile(user.id)
    if not p["skin_tone"]:
        raise ApiError("VALIDATION_ERROR", "Save the skin tone on screen 14 first.", 409)
    best = brow_shades(p["skin_tone"], p["undertone"] or "neutral")["best"]
    colour = body.preferred_colour or best
    if colour not in C.COLOUR_BY_ID:
        raise ApiError("VALIDATION_ERROR", f"Unknown colour '{colour}'.", 422)
    update_profile(user.id, skin_tone_confirmed=True, preferred_colour=colour)
    return {"next_screen": "16", "preferred_colour": C.COLOUR_BY_ID[colour]}


class DirectionIn(BaseModel):
    direction: Optional[Literal["refined_natural", "precise_defined", "show_me"]] = Field(
        None, description="Leave empty for \"I'll add this later\" (16 -> 18).")


@router.put("/v1/onboarding/direction", tags=["Onboarding 14-18"],
            summary="16 BEGIN (returns screen 17) or skip (goes to 18)")
def direction(body: DirectionIn, user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    if body.direction is None:
        update_profile(user.id, style_direction=None, direction_skipped=True)
        return {"next_screen": "18", "skipped": True}
    d = C.STYLE_DIRECTIONS[body.direction]
    update_profile(user.id, style_direction=body.direction, direction_skipped=False,
                   preferred_style=d["first_style"] or get_profile(user.id)["preferred_style"])
    return {"next_screen": "17", "screen_17": {
        "title": d["name"], "line": "This shapes your recommendations from the start.",
        "points": d["confirmation"], "first_style": d["first_style"],
        "default_intensity": d["default_intensity"], "default_mode": d["default_mode"],
        "provisional": d["provisional"],
        "cta": "THIS IS MY DIRECTION", "alt": "Choose a different direction"}}


class CompleteIn(BaseModel):
    carry_style: Optional[str] = Field(None, description="Style a guest chose before signing up (13 / 13a). "
                                                         "ENTER ARCH then opens 29 with it selected.")


@router.post("/v1/onboarding/complete", tags=["Onboarding 14-18"], summary="18 ENTER ARCH: summary + next screen")
def complete(body: CompleteIn, user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    p = get_profile(user.id)
    user.doc.setdefault("flags", {})["onboarding_complete"] = True
    save_user(user)
    if body.carry_style:
        update_profile(user.id, preferred_style=body.carry_style)
    goal = next((g["name"] for g in C.BROW_GOALS if g["id"] == p["brow_goal"]), None)
    tone = C.SKIN_TONE_BY_ID.get(p["skin_tone"] or "", {})
    return {
        "screen_18": {"label": "COMPLETE", "title": "YOUR PROFILE IS SET", "line": "From here, the work is yours.",
                      "skin_tone": f"{tone.get('name', '')} {p['undertone'] or ''}".strip() or None,
                      "brow_goal": goal,
                      "style_direction": C.STYLE_DIRECTIONS[p["style_direction"]]["name"] if p["style_direction"] else None,
                      "edit": "Edit your selections", "footer": "Your choices can be refined as you go."},
        "next_screen": "29" if body.carry_style else "19",
        "selected_style": body.carry_style,
    }


@router.get("/v1/profile", tags=["Onboarding 14-18"], summary="Brow profile")
def profile(user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    return get_profile(user.id)


# -------------------------------------------------------------------- home

@router.get("/v1/home", tags=["Home 12, 19-21"], summary="Which home to show and its data")
def home(user: User = Depends(current_user)):
    if user.is_guest:
        return {"screen": "12", "variant": "guest",
                "tiles": [{"title": "Brow styles", "sub": "ALL EIGHT, TO BROWSE", "to": "12a"},
                          {"title": "How ARCH works", "sub": "A SHORT GUIDED LOOK", "to": "61"},
                          {"title": "Your face, read precisely", "sub": "Begins with an account", "to": "13"}]}
    flags = user.doc.get("flags", {})
    if not flags.get("onboarding_complete"):
        return {"screen": "14", "variant": "onboarding"}
    looks = db.list_for_user("looks", user.id, limit=1)
    actions = [{"title": "Try a brow style", "to": "22"},
               {"title": "Draw your tracing guide", "to": "45"},
               {"title": "Get a recommendation", "to": "39"}]
    if looks:
        lk = looks[0]
        return {"screen": "21", "variant": "returning_personalised", "name": user.name,
                "last_look": {"look_id": lk["id"], "caption": lk["caption"],
                              "saved": f"Saved {_date(lk['created_at'])}", "image_url": lk["images"]["face"],
                              "reapply_to": "36"},
                "quick_actions": [{"title": "NEW SCAN", "to": "22"}, {"title": "MY LOOKS", "to": "50"}],
                "home_returning": {"screen": "20", "actions": actions}}
    return {"screen": "19", "variant": "new_user", "actions": actions +
            [{"title": "Read my brows", "to": "22", "to_confirm": True}]}


# ----------------------------------------------------------------- consent (M2)

class ConsentRecordIn(BaseModel):
    type: Literal["biometric_notice", "face_scan"] = Field(..., description="02 = biometric_notice, 23 = face_scan")
    granted: bool = Field(True, description="false withdraws the live consent of this type")
    boxes: Optional[dict] = Field(None, description="Screen 02: biometric_data, privacy_policy, terms_of_use, age_18 "
                                                    "(all must be true)")
    policy_version: Optional[str] = Field(None, description="Defaults to the current policy version")


def _install(x_install_id: Optional[str]):
    return (x_install_id or "").strip()[:100] or None


@router.post("/v1/consent", tags=["Consent 02, 23"], status_code=201,
             summary="02 CONTINUE (before sign-up: send X-Install-Id) / 23 ALLOW CAMERA")
def record_consent(body: ConsentRecordIn, user: User = Depends(current_user),
                   x_install_id: Optional[str] = Header(None, description="App install id (screen 02 before sign-up)")):
    uid = None if user.is_guest else user.id
    if not body.granted:
        if not uid:
            raise ApiError("ACCOUNT_REQUIRED", "This needs an account.", 403, {"route_to": "13a"})
        rec = CS.withdraw(body.type, uid, by="user")
        return {"consent": rec, "status": CS.status_of(rec)}
    rec = CS.grant(body.type, uid, _install(x_install_id), body.boxes, body.policy_version)
    nxt = "03" if body.type == "biometric_notice" else "25"
    return {"consent": rec, "status": "granted", "next_screen": nxt}


@router.get("/v1/consent/status", tags=["Consent 02, 23"],
            summary="none / granted / withdrawn for 02 and 23; show_screen_23 says whether to show 23")
def consent_status(user: User = Depends(current_user),
                   x_install_id: Optional[str] = Header(None)):
    return CS.status(None if user.is_guest else user.id, _install(x_install_id))


class ConsentIn(BaseModel):
    granted: bool = Field(..., description="The FACE SCAN CONSENT tick on screen 23.")


@router.post("/v1/consents/face-scan", tags=["Consent 02, 23"],
             summary="23 ALLOW CAMERA (legacy alias of POST /v1/consent type=face_scan)")
def face_scan_consent(body: ConsentIn, user: User = Depends(current_user)):
    require(user, "scan", gate="13")
    if body.granted:
        rec = CS.grant("face_scan", user.id, None)
    else:
        rec = CS.withdraw("face_scan", user.id, by="user")
    return {"consent": rec, "next_screen": "25" if body.granted else "22"}


@router.get("/v1/consents", tags=["Consent 02, 23"], summary="Every consent record on her account")
def consents(user: User = Depends(current_user)):
    require(user, "account", gate="13a")
    return {"consents": db.list_for_user("consents", user.id, limit=1000)}


def has_face_scan_consent(user) -> bool:
    return CS.face_scan_ok(user.id)
