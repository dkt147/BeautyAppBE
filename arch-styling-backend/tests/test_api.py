"""Run:  pytest -q
Scan / try-on tests need a face photo:  set ARCH_TEST_PHOTO=path/to/face.jpg
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.catalogue.measurements import load_measurements
from app.main import app
from app.rendering.geometry import check_profile, style_profile

c = TestClient(app)
PHOTO = os.getenv("ARCH_TEST_PHOTO")


def H():
    """A fresh signed-up account (M1), as a bearer header."""
    tag = uuid.uuid4().hex[:8]
    r = c.post("/v1/auth/register", json={"name": "Mary", "email": f"t-{tag}@example.com",
                                          "password": "a-good-password", "confirm_password": "a-good-password"})
    assert r.status_code == 201, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


# ---------------------------------------------------------- spec fidelity

@pytest.mark.parametrize("sid", list(load_measurements().styles))
def test_geometry_matches_measurement_json(sid):
    st = load_measurements().style(sid)
    chk = check_profile(st, style_profile(st))
    assert abs(chk["length_ew"] - st.length_ew) < 0.01
    assert abs(chk["tail_vs_head_offset_ew"] - st.tail_offset_ew) < 0.02
    assert abs(chk["thickness_body_ew"] - st.thickness_body_ew) < 0.02
    assert abs(chk["thickness_tail_ew"] - st.thickness_tail_ew) < 0.02
    if st.peak_type != "level":
        assert abs(chk["peak_height_ew"] - st.peak_height_ew) < 0.015
        assert abs(chk["peak_position_pct"] - st.peak_position_pct) <= 2.0


def test_face_shape_table_and_peak_adjustment():
    M = load_measurements()
    assert M.face_shape("oval").recommended_style == "arch"
    assert M.peak_pct("sharp", "round") == 71          # 65 + 6
    assert M.peak_pct("rounded", "square") == 45       # 52 - 7
    assert M.peak_pct("straight", "oblong") is None    # no peak
    assert M.plateau("rounded", "square") == (35, 55)


# ---------------------------------------------------------------- routes

def test_health_and_catalogue():
    assert c.get("/health").json()["status"] == "ok"
    st = c.get("/v1/styles").json()["styles"]
    assert [s["id"] for s in st] == ["arch", "structured", "feathered", "bold", "straight", "micro", "sharp", "rounded"]
    assert len(c.get("/v1/colours").json()["colours"]) == 8
    assert [i["id"] for i in c.get("/v1/intensities").json()["intensities"]] == ["understated", "defined", "deliberate"]
    assert c.get("/v1/styles/arch/diagram.png").status_code == 200


def test_guest_gates():
    g = {"X-Guest": "true"}
    assert c.get("/v1/home", headers=g).json()["screen"] == "12"
    r = c.post("/v1/consents/face-scan", json={"granted": True}, headers=g)
    assert r.status_code == 403 and r.json()["route_to"] == "13"
    r = c.post("/v1/looks", json={"scan_id": "x", "style": "arch"}, headers=g)
    assert r.json()["route_to"] == "13a"


def test_onboarding_flow():
    h = H()
    assert c.get("/v1/home", headers=h).json()["screen"] == "14"
    s15 = c.put("/v1/onboarding/skin-tone-goal", json={"skin_tone": "medium", "undertone": "warm",
                                                       "brow_goal": "colour"}, headers=h).json()["screen_15"]
    assert s15["brow_shades"][0]["role"] == "Best" and len(s15["brow_shades"]) == 3
    assert c.post("/v1/onboarding/confirm-tone", json={}, headers=h).json()["next_screen"] == "16"
    s17 = c.put("/v1/onboarding/direction", json={"direction": "refined_natural"}, headers=h).json()
    assert s17["screen_17"]["points"][0] == "Arch presented first"
    done = c.post("/v1/onboarding/complete", json={"carry_style": "structured"}, headers=h).json()
    assert done["next_screen"] == "29" and done["screen_18"]["brow_goal"] == "Colour"
    assert c.get("/v1/home", headers=h).json()["screen"] == "19"


def test_scan_needs_consent():
    r = c.post("/v1/scans", files={"photo": ("a.jpg", b"123", "image/jpeg")}, headers=H())
    assert r.json()["code"] == "CONSENT_REQUIRED"


def test_bad_image_routes_to_26():
    h = H()
    c.post("/v1/consents/face-scan", json={"granted": True}, headers=h)
    r = c.post("/v1/scans", files={"photo": ("a.jpg", b"not an image", "image/jpeg")}, headers=h)
    assert r.json()["route_to"] == "26"


@pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")
def test_full_styling_journey():
    h = H()
    c.post("/v1/consents/face-scan", json={"granted": True}, headers=h)
    with open(PHOTO, "rb") as f:
        sc = c.post("/v1/scans", files={"photo": ("f.jpg", f, "image/jpeg")}, headers=h).json()
    sid = sc["scan_id"]
    M = load_measurements()
    fs = M.face_shape(sc["face_shape"]["id"])
    assert sc["recommendation"]["recommended"]["style"] == fs.recommended_style
    assert sc["recommendation"]["alternate"]["style"] == fs.alternate_style
    flagged = [s["id"] for s in c.get("/v1/styles", params={"scan_id": sid}, headers=h).json()["styles"]
               if s["recommended_for_you"]]
    assert set(flagged) == {fs.recommended_style, fs.alternate_style}
    for mode in ("reshape", "refine"):
        r = c.post("/v1/tryon/render", json={"scan_id": sid, "style": "structured", "intensity": "defined",
                                             "mode": mode}, headers=h).json()
        assert c.get(r["images"]["face"]).status_code == 200
    assert len(c.post("/v1/tryon/intensities", json={"scan_id": sid, "style": "arch"}, headers=h).json()["items"]) == 3
    cmp_ = c.post("/v1/tryon/compare", json={"scan_id": sid, "style": "arch",
                                             "intensities": ["defined", "deliberate"]}, headers=h).json()
    assert cmp_["looks"][0]["cta"] == "I CHOOSE DEFINED"
    lk = c.post("/v1/looks", json={"scan_id": sid, "style": "structured", "intensity": "defined",
                                    "colour": "dark_brown"}, headers=h).json()
    assert lk["screen_38"]["editorial_title"] == "The One She Keeps Returning To"
    assert lk["look"]["name"] == "Structured · Defined · Dark Brown"
