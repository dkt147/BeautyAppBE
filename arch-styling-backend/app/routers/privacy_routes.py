"""Screens 39, 55 to 55f and 78 to 80: brow profile, Delete my face scan and
account deletion (M4 + M12)."""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app import config
from app.core.auth import User, current_user, require
from app.core.devtools import IS_DEV, dev_only
from app.core.errors import ApiError
from app.services import privacy_service as P

router = APIRouter()
TAG = "Brow profile & privacy 39, 55-55f, 78-80"


def _account(user: User) -> User:
    require(user, "account", gate="13a")
    return user


@router.get("/v1/me/brow-profile", tags=[TAG],
            summary="55 Brow Profile (55f when has_scan is false). has_scan + last_scan_date drive 22a and 39")
def get_brow_profile(user: User = Depends(current_user)):
    return P.brow_profile(_account(user).id)


class BrowProfileIn(BaseModel):
    face_shape: Optional[str] = Field(None, description="55a Face shape: one of the seven. Used for her recommendations")
    preferred_style: Optional[str] = Field(None, description="Preferred style → on 55a")
    preferred_colour: Optional[str] = Field(None, description="Preferred colour → on 55a")
    skin_tone: Optional[str] = Field(None, description="fair / light / medium / tan / deep / rich. Re-runs the "
                                                       "library and recommendations on her existing scan")
    undertone: Optional[str] = Field(None, description="warm / neutral / cool")


@router.patch("/v1/me/brow-profile", tags=[TAG], summary="55a SAVE CHANGES -> 55 (route to confirm)")
def patch_brow_profile(body: BrowProfileIn, user: User = Depends(current_user)):
    out = P.update_brow_profile(_account(user).id, body.preferred_style, body.preferred_colour,
                                body.face_shape, body.skin_tone, body.undertone)
    return {**out, "next_screen": "55", "route_to_confirm": True}


class DeleteScanIn(BaseModel):
    remove_photographs: bool = Field(..., description="55c: REMOVE PHOTOGRAPHS TOO (true) or KEEP MY PHOTOGRAPHS (false)")


@router.delete("/v1/me/face-scan", tags=[TAG],
               summary="55c answered -> 55d / 55e. Removes measurements, brow profile, scan photos; withdraws consent")
def delete_face_scan(body: DeleteScanIn, user: User = Depends(current_user)):
    return P.delete_face_scan(_account(user).id, body.remove_photographs)


class DeleteAccountIn(BaseModel):
    confirm: bool = Field(..., description="79 YES, DELETE MY ACCOUNT")


@router.post("/v1/me/delete", tags=[TAG],
             summary="79 YES, DELETE MY ACCOUNT -> 80. Purged after 14 days; signing in stops it")
def delete_account(body: DeleteAccountIn, user: User = Depends(current_user)):
    _account(user)
    if not body.confirm:
        raise ApiError("VALIDATION_ERROR", "Confirm the deletion on screen 79.", 422)
    return P.start_account_deletion(user.doc)


@router.post("/v1/dev/run-jobs", tags=["Dev tools"], dependencies=[Depends(dev_only)], include_in_schema=IS_DEV,
             summary="Run the scheduled privacy jobs now (purge due accounts, retention sweep)")
def run_jobs(user: User = Depends(current_user)):
    from app.services.billing_service import run_billing_jobs
    return {"purged": P.purge_due(), "retention": P.retention_sweep(), "billing": run_billing_jobs()}
