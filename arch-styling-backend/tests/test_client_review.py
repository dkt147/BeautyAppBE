"""Client review, 19 November 2026 (Chi): Bold ran past the ear, and the
tracing guide showed a flat brown patch instead of a line to trace.
Scan-based tests need a face photo: set ARCH_TEST_PHOTO=path/to/face.jpg."""
import uuid

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.catalogue.measurements import load_measurements
from app.catalogue.recommend_copy import FACE_OVAL
from app.core import db
from app.main import app
from app.rendering.brow_renderer import FACE_EDGE_MARGIN_EW, BrowRenderer
from app.rendering.geometry import check_profile, style_profile
from app.services.scan_service import load_scan_assets
from tests.test_final import PHOTO, member, stored_scan

c = TestClient(app)
PW = "a-good-password"
M = load_measurements()


def account():
    e = f"cr-{uuid.uuid4().hex[:8]}@example.com"
    j = c.post("/v1/auth/register", json={"name": "Mary", "email": e, "password": PW, "confirm_password": PW}).json()
    return j["user"]["id"], {"Authorization": "Bearer " + j["access_token"]}


# ------------------------------------------------------------- Bold length

def test_bold_length_is_1_80_and_profile_matches():
    st = M.style("bold")
    assert st.length_ew == 1.8
    assert abs(check_profile(st, style_profile(st))["length_ew"] - 1.8) < 0.01
    assert st.length_ew < M.style("straight").length_ew                     # no longer the longest style


def _scan_with_photo(h):
    c.post("/v1/consent", json={"type": "face_scan"}, headers=h)
    with open(PHOTO, "rb") as f:
        r = c.post("/v1/scans", files={"photo": ("f.jpg", f, "image/jpeg")}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["scan_id"]


@pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")
@pytest.mark.parametrize("mode", ["reshape", "refine"])
def test_every_style_ends_inside_the_face(mode):
    uid, h = account()
    scan = db.get("scans", _scan_with_photo(h))
    image, lm, naturals = load_scan_assets(scan)
    fs = scan["face_shape"]["id"]
    for sid in M.styles:
        geos = BrowRenderer().guide(image, lm, M.style(sid), M.peak_pct(sid, fs), M.plateau(sid, fs), mode, naturals)
        for side, g in geos.items():
            ew = naturals[side].ew
            oval = g["frame"].to_local(lm[FACE_OVAL, :2])
            band = oval[(oval[:, 1] >= g["bottom"].min() - 0.6 * ew) & (oval[:, 1] <= g["top"].max() + 0.6 * ew)
                        & (oval[:, 0] > 0)]
            assert g["s"][-1] <= band[:, 0].max() - FACE_EDGE_MARGIN_EW * ew + 1e-6, (sid, side)


# ------------------------------------------------------- tracing strokes

@pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")
def test_strokes_endpoint_returns_guide_line_on_her_face():
    uid, h = account()
    member(h)
    sid = _scan_with_photo(h)
    for finish in ("full", "ombre"):
        s = c.post("/v1/tracing/sessions", headers=h, json={
            "scan_id": sid, "style": "bold", "colour": "dark_brown", "intensity": "defined",
            "mode": "reshape", "finish": finish})
        assert s.status_code == 201, s.text
        r = c.get(f"/v1/tracing/sessions/{s.json()['session']['id']}/strokes", headers=h)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["style"] == "bold" and j["finish"] == finish
        pts = j["strokes"]
        assert len(pts) >= 100 and {p["brow"] for p in pts} == {"right", "left"}
        assert all(0 < p["x"] < 1 and 0 < p["y"] < 1 for p in pts)
        assert set(pts[0]) >= {"x", "y"}
        for side in ("right", "left"):
            b = j["brows"][side]
            assert b["outline"][0]["u"] == 0 and b["outline"][len(b["outline"]) // 2 - 1]["u"] == 1
            op = [p["opacity"] for p in b["centre_line"]]
            if finish == "ombre":
                assert op[0] < 0.5 and op[-1] == 1.0 and op == sorted(op)     # lighter head, full tail
            else:
                assert set(op) == {1.0}
        r_x = [p["x"] for p in j["brows"]["right"]["outline"]]
        l_x = [p["x"] for p in j["brows"]["left"]["outline"]]
        assert max(r_x) < min(l_x) or max(l_x) < min(r_x)                     # two separate brows


def test_strokes_need_a_scan_and_the_owner():
    uid, h = account()
    member(h)
    sid = stored_scan(uid)                       # synthetic scan, no brow reading
    db.set_fields("scans", sid, {"recommendation": {"colour": {"id": "taupe"}, "intensity": "defined"}})
    s = c.post("/v1/tracing/sessions", headers=h, json={
        "scan_id": sid, "style": "arch", "colour": "dark_brown", "intensity": "defined",
        "mode": "reshape", "finish": "full"})
    assert s.status_code == 201, s.text
    tid = s.json()["session"]["id"]
    r = c.get(f"/v1/tracing/sessions/{tid}/strokes", headers=h)
    assert r.status_code == 409 and r.json()["code"] == "SCAN_REQUIRED" and r.json()["route_to"] == "22"
    _, h2 = account()
    member(h2)
    assert c.get(f"/v1/tracing/sessions/{tid}/strokes", headers=h2).status_code == 404


def test_strokes_members_only():
    _, h = account()
    r = c.get("/v1/tracing/sessions/trc_nope/strokes", headers=h)
    assert r.json()["code"] == "MEMBERSHIP_REQUIRED"


@pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")
def test_strokes_field_definitions():
    """BACKEND_FIXES Round 6 item 25 (a) to (d), checked against the scan's landmarks."""
    from app.vision.landmarks import EYE, eye_frame, eye_width
    uid, h = account()
    member(h)
    sid = _scan_with_photo(h)
    s = c.post("/v1/tracing/sessions", headers=h, json={
        "scan_id": sid, "style": "arch", "colour": "dark_brown", "intensity": "defined",
        "mode": "reshape", "finish": "full"}).json()
    j = c.get(f"/v1/tracing/sessions/{s['session']['id']}/strokes", headers=h).json()
    scan = db.get("scans", sid)
    _, lm, _ = load_scan_assets(scan)
    W, H = j["image"]["width"], j["image"]["height"]
    for side in ("right", "left"):
        ew = eye_width(lm, side)                                             # (c) corner to corner
        fr = eye_frame(lm, side)
        for p in j["brows"][side]["outline"]:
            assert set(p) >= {"x", "y", "u", "edge", "s_ew", "n_ew"} and p["edge"] in ("top", "bottom")   # (b)
            px = fr.to_image(p["s_ew"] * ew, p["n_ew"] * ew)
            assert abs(px[0] / W - p["x"]) < 0.002 and abs(px[1] / H - p["y"]) < 0.002
        assert all(q["opacity"] == 1.0 for q in j["brows"][side]["centre_line"])                       # (d) Full
    # (a) "right" = landmarks 133/33 = the person's right eye = image LEFT of a non-mirrored photo
    assert (EYE["right"]["inner"], EYE["right"]["outer"]) == (133, 33)
    rx = np.mean([p["x"] for p in j["brows"]["right"]["outline"]])
    lx = np.mean([p["x"] for p in j["brows"]["left"]["outline"]])
    assert rx < lx
