"""Screens 36a, 73 to 77 and 45 to 49b: tracing sessions and hand-drawn
guides (M9). Live tracing runs on the device; these calls record it."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field

from app import config
from app.core import db
from app.core.auth import User, current_user, require
from app.core.errors import ApiError
from app.routers.styling_routes import Colour, Finish, Intensity, Mode, Style, _resolve
from app.services import tracing_service as T
from app.services.scan_service import get_scan

router = APIRouter()
TAG = "Tracing 36a, 45-49b, 73-77"


def _member(user: User) -> User:
    # Members only (build plan M9). Until M10 lands every account passes;
    # then non-members get MEMBERSHIP_REQUIRED -> 64 here, before 73.
    require(user, "trace", gate="13")
    return user


class SessionIn(BaseModel):
    look_id: Optional[str] = Field(None, description="Tracing a look saved on 37 (the trace attaches to it)")
    scan_id: Optional[str] = Field(None, description="Tracing the look on 36 before saving")
    style: Optional[Style] = None
    colour: Optional[Colour] = None
    intensity: Optional[Intensity] = None
    mode: Optional[Mode] = Field(None, description="Reshape mine = SCULPT, Refine mine = REFINE (fixed once started)")
    finish: Optional[Finish] = None


@router.post("/v1/tracing/sessions", status_code=201, tags=[TAG],
             summary="36a BEGIN (the gate fires here) -> 73. Type follows the mode on leaving 36")
def start_session(body: SessionIn, user: User = Depends(current_user)):
    _member(user)
    if body.look_id:
        lk = db.get("looks", body.look_id)
        if not lk or lk["user_id"] != user.id or not lk.get("style"):
            raise ApiError("NOT_FOUND", "Look not found.", 404)
        scan = db.get("scans", lk["scan_id"]) if lk.get("scan_id") else None
        recipe = {k: lk[k] for k in ("style", "colour", "intensity", "mode")}
        recipe["finish"] = lk.get("finish") or "full"
        if body.mode and body.mode != recipe["mode"]:
            recipe["mode"] = body.mode
        return T.start(user, recipe, look_id=lk["id"], scan=scan)
    if not (body.scan_id and body.style):
        raise ApiError("VALIDATION_ERROR", "Send look_id, or scan_id with style.", 422)
    scan = get_scan(user, body.scan_id)
    v, src = _resolve(user, scan, body)
    recipe = {"style": body.style, **v}
    return {**T.start(user, recipe, scan=scan), "resolved_from": src}


class SessionUpdateIn(BaseModel):
    stage: Optional[str] = Field(None, examples=["75-03"], description="Stage reached (forward only)")
    event: Optional[Literal["interrupted", "resumed", "light_low", "tracking_lost", "hand_occlusion", "recovered",
                            "landscape", "portrait", "tracking_failed", "paused"]] = None
    mode: Optional[Mode] = Field(None, description="Rejected if it would change the session type")


@router.patch("/v1/tracing/sessions/{session_id}", tags=[TAG],
              summary="75-xx / 76-xx stage reached, or an event (75a, 75b, 75c, 75e, 75f, 49c)")
def update_session(session_id: str, body: SessionUpdateIn, user: User = Depends(current_user)):
    _member(user)
    if not (body.stage or body.event or body.mode):
        raise ApiError("VALIDATION_ERROR", "Send a stage or an event.", 422)
    return T.update(user, session_id, body.stage, body.event, body.mode)


@router.get("/v1/tracing/sessions/{session_id}", tags=[TAG], summary="One tracing session")
def get_session(session_id: str, user: User = Depends(current_user)):
    _member(user)
    return {"session": T._public(T._get(user, session_id)), "stages": T.stages(T._get(user, session_id)["type"])}


@router.post("/v1/tracing/sessions/{session_id}/complete", tags=[TAG],
             summary="FINISH -> 77 (state 2 if the look was saved on 37, else state 1)")
def complete_session(session_id: str, user: User = Depends(current_user)):
    _member(user)
    return T.complete(user, session_id)


class SaveTracedIn(BaseModel):
    name: Optional[str] = Field(None, max_length=60)


@router.post("/v1/tracing/sessions/{session_id}/save", tags=[TAG],
             summary="77 SAVE LOOK (state 1 -> 2): a new TRACED look")
def save_traced(session_id: str, body: SaveTracedIn, user: User = Depends(current_user)):
    _member(user)
    return T.save_traced_look(user, session_id, body.name)


@router.post("/v1/tracing/sessions/{session_id}/leave", tags=[TAG], summary="75d LEAVE SESSION -> 36")
def leave_session(session_id: str, user: User = Depends(current_user)):
    _member(user)
    return T.leave(user, session_id)


# ------------------------------------------------------------------ guides

@router.post("/v1/guides", status_code=201, tags=[TAG],
             summary="49a SAVE THIS GUIDE -> 49b (also a TRACED look in My Looks)")
async def save_guide(strokes: str = Form(..., description='JSON: {"left": [[[x, y], ...]], "right": [...]}, '
                                                          "points 0 to 1 over the guide photo"),
                     name: Optional[str] = Form(None, description="GUIDE NAME on 49a"),
                     image: Optional[UploadFile] = File(None, description="The drawn guide (PNG / JPEG), optional"),
                     user: User = Depends(current_user)):
    _member(user)
    data = None
    if image is not None:
        limit = int(config.MAX_UPLOAD_MB * 1024 * 1024)
        data = await image.read(limit + 1)
        if len(data) > limit:
            raise ApiError("IMAGE_TOO_LARGE", f"The image is larger than {config.MAX_UPLOAD_MB:g} MB.", 413)
    return T.save_guide(user, name, T.parse_strokes(strokes), data or None)


@router.get("/v1/guides", tags=[TAG], summary="Her saved guides")
def list_guides(user: User = Depends(current_user)):
    _member(user)
    return {"guides": db.list_for_user("guides", user.id, limit=1000)}


@router.get("/v1/guides/{guide_id}", tags=[TAG], summary="One guide with its strokes")
def get_guide(guide_id: str, user: User = Depends(current_user)):
    _member(user)
    return {"guide": T.get_guide(user, guide_id)}


@router.delete("/v1/guides/{guide_id}", tags=[TAG], summary="Delete a guide (and its look)")
def delete_guide(guide_id: str, user: User = Depends(current_user)):
    _member(user)
    return T.delete_guide(user, guide_id)
