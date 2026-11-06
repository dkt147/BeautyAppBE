"""Screens 12a, 29 (no-scan preview) and 89 to 94: catalogue and brow library (M5)."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.core.auth import User, current_user
from app.services import library_service as L
from app.services.profile_service import get_profile

router = APIRouter()
TAG = "Catalogue & library 12a, 29, 89-94"


@router.get("/v1/catalogue", tags=[TAG], summary="Styles, intensities, tones, colours, finishes and modes in one call")
def catalogue():
    return L.catalogue()


@router.get("/v1/library", tags=[TAG],
            summary="89-94 The Library (page=1..6 -> screen 89..94); with style=, the no-scan preview on 29")
def library(tone: Optional[str] = Query(None, description="Skin tone. Empty = her brow profile tone"),
            finish: Literal["full", "ombre"] = Query("full", description="Full is the base finish"),
            style: Optional[str] = Query(None, description="Only this style (29 no-scan preview)"),
            page: Optional[int] = Query(None, description="1 to 6, four cards per page"),
            user: User = Depends(current_user)):
    t, src = L.resolve_tone(tone, None if user.is_guest else get_profile(user.id))
    return {**L.library(t, finish, style, page), "tone_from": src}


@router.get("/v1/library/editorial", tags=[TAG], summary="The 24 editorial titles (display undecided, question 16)")
def editorial():
    return L.editorial()
