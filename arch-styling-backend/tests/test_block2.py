"""Block 2: M2 consent, M4 brow profile + Delete my face scan + F10 uploads,
M12 account deletion, M5 library, M7 finish + before/after, M9 tracing."""
import json
import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from app import config
from app.core import db
from app.main import app
from app.services import privacy_service as P
from app.services import render_service as RS
from app.services import tracing_service as T
from app.core.auth import User
from app.core.media import path_of

c = TestClient(app)
PW = "a-good-password"
PHOTO = os.getenv("ARCH_TEST_PHOTO")
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
BOXES = {"biometric_data": True, "privacy_policy": True, "terms_of_use": True, "age_18": True}


def account(install=None):
    e = f"b2-{uuid.uuid4().hex[:8]}@example.com"
    h = {"X-Install-Id": install} if install else {}
    r = c.post("/v1/auth/register", json={"name": "Mary", "email": e, "password": PW, "confirm_password": PW},
               headers=h)
    assert r.status_code == 201, r.text
    j = r.json()
    return e, j["user"]["id"], {"Authorization": "Bearer " + j["access_token"]}


def member(h):
    """Make the signed-in account a member (dev grant, no store)."""
    r = c.post("/v1/dev/grant-membership", json={"plan": "annual", "status": "trial"}, headers=h)
    assert r.status_code == 200 and r.json()["is_member"], r.text


def fake_scan(uid, face_shape="oval"):
    """A stored scan without running the vision pipeline."""
    sid = db.new_id("scan")
    d = config.MEDIA_DIR / "scans" / sid
    d.mkdir(parents=True, exist_ok=True)
    (d / "photo.jpg").write_bytes(b"\xff\xd8\xff fake")
    db.put("scans", sid, uid, {"id": sid, "user_id": uid, "created_at": time.time(),
                               "image": {"url": config.media_url(f"scans/{sid}/photo.jpg")},
                               "face_shape": {"id": face_shape}})
    from app.services.profile_service import update_profile
    update_profile(uid, face_shape=face_shape, last_scan_id=sid, last_scan_at=time.time())
    return sid


def fake_look(uid, with_photo=True, mode="reshape"):
    lid = db.new_id("look")
    images = None
    if with_photo:
        d = config.MEDIA_DIR / "looks" / lid
        d.mkdir(parents=True, exist_ok=True)
        (d / "face.jpg").write_bytes(b"\xff\xd8\xff")
        images = {"face": config.media_url(f"looks/{lid}/face.jpg")}
    db.put("looks", lid, uid, {"id": lid, "user_id": uid, "created_at": time.time(), "scan_id": None,
                               "style": "arch", "colour": "dark_brown", "intensity": "defined", "mode": mode,
                               "finish": "full", "name": "Arch · Defined · Dark Brown",
                               "mode_label": "RESHAPE MINE", "images": images})
    return lid


def DELETE(url, body, headers):
    return c.request("DELETE", url, json=body, headers=headers)


# ================================================================ M2 consent

def test_screen_02_before_signup_then_linked():
    install = "inst-" + uuid.uuid4().hex[:6]
    hi = {"X-Install-Id": install}
    r = c.post("/v1/consent", json={"type": "biometric_notice", "boxes": {"biometric_data": True}}, headers=hi)
    assert r.status_code == 422 and len(r.json()["details"]) == 3          # CONTINUE needs all four
    r = c.post("/v1/consent", json={"type": "biometric_notice", "boxes": BOXES}, headers=hi)
    assert r.status_code == 201 and r.json()["next_screen"] == "03"
    st = c.get("/v1/consent/status", headers=hi).json()
    assert st["biometric_notice"]["status"] == "granted" and st["show_screen_02"] is False
    assert c.post("/v1/consent", json={"type": "biometric_notice", "boxes": BOXES}).status_code == 422  # no install id
    _, uid, h = account(install)
    recs = c.get("/v1/consents", headers=h).json()["consents"]
    assert [r["type"] for r in recs] == ["biometric_notice"] and recs[0]["policy_version"] == config.POLICY_VERSION


def test_face_scan_consent_none_granted_withdrawn():
    _, uid, h = account()
    st = c.get("/v1/consent/status", headers=h).json()
    assert st["face_scan"]["status"] == "none" and st["show_screen_23"] is True
    assert c.post("/v1/consent", json={"type": "face_scan"}, headers={"X-Guest": "true"}).json()["route_to"] == "13"
    assert c.post("/v1/consent", json={"type": "face_scan"}, headers=h).json()["next_screen"] == "25"
    st = c.get("/v1/consent/status", headers=h).json()
    assert st["face_scan"]["status"] == "granted" and st["show_screen_23"] is False
    w = c.post("/v1/consent", json={"type": "face_scan", "granted": False}, headers=h).json()
    assert w["status"] == "withdrawn"
    assert c.get("/v1/consent/status", headers=h).json()["show_screen_23"] is True
    r = c.post("/v1/scans", files={"photo": ("a.jpg", b"\xff\xd8\xffx", "image/jpeg")}, headers=h)
    assert r.json()["code"] == "CONSENT_REQUIRED" and r.json()["route_to"] == "23"


def test_screen_23_flag(monkeypatch):
    _, uid, h = account()
    monkeypatch.setattr(config, "SCREEN_23_ENABLED", False)
    st = c.get("/v1/consent/status", headers=h).json()
    assert st["show_screen_23"] is False and st["screen_23_enabled"] is False
    r = c.post("/v1/scans", files={"photo": ("a.jpg", b"not an image", "image/jpeg")}, headers=h)
    assert r.json()["code"] == "BAD_IMAGE"                                # got past the consent check


# ============================================================= F10 uploads

def test_upload_limits(monkeypatch):
    _, uid, h = account()
    c.post("/v1/consent", json={"type": "face_scan"}, headers=h)
    r = c.post("/v1/scans", files={"photo": ("a.gif", b"GIF89a", "image/gif")}, headers=h)
    assert r.status_code == 415 and r.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"
    monkeypatch.setattr(config, "MAX_UPLOAD_MB", 0.001)
    r = c.post("/v1/scans", files={"photo": ("a.jpg", b"\xff\xd8\xff" + b"0" * 5000, "image/jpeg")}, headers=h)
    assert r.status_code == 413 and r.json()["code"] == "IMAGE_TOO_LARGE"


# ====================================================== M4 brow profile (55)

def test_brow_profile_55_55f_and_55a():
    _, uid, h = account()
    bp = c.get("/v1/me/brow-profile", headers=h).json()
    assert bp["screen"] == "55f" and bp["has_scan"] is False and bp["face_shape"] is None
    fake_scan(uid, "heart")
    bp = c.get("/v1/me/brow-profile", headers=h).json()
    assert bp["screen"] == "55" and bp["face_shape"]["name"] == "Heart" and bp["last_scan"]["date"]
    up = c.patch("/v1/me/brow-profile", json={"preferred_style": "rounded", "preferred_colour": "chestnut"},
                 headers=h).json()
    assert up["preferred_style"]["name"] == "Rounded" and up["preferred_colour"]["id"] == "chestnut"
    assert up["next_screen"] == "55"
    assert c.patch("/v1/me/brow-profile", json={"preferred_style": "nope"}, headers=h).status_code == 422
    assert c.patch("/v1/me/brow-profile", json={}, headers=h).status_code == 422
    assert c.get("/v1/me/brow-profile", headers={"X-Guest": "true"}).json()["route_to"] == "13a"


@pytest.mark.parametrize("remove", [True, False])
def test_delete_my_face_scan(remove):
    _, uid, h = account()
    c.post("/v1/consent", json={"type": "face_scan"}, headers=h)
    sid = fake_scan(uid)
    lid = fake_look(uid)
    c.patch("/v1/me/brow-profile", json={"preferred_style": "arch"}, headers=h)
    r = DELETE("/v1/me/face-scan", {"remove_photographs": remove}, h).json()
    assert r["screen"] == ("55d" if remove else "55e") and r["deleted"]["scans"] == 1
    assert db.get("scans", sid) is None and not (config.MEDIA_DIR / "scans" / sid).exists()
    lk = db.get("looks", lid)
    assert lk["style"] == "arch"                                           # the recipe stays
    assert (lk["images"] is None) == remove
    assert (config.MEDIA_DIR / "looks" / lid).exists() != remove
    st = c.get("/v1/consent/status", headers=h).json()
    assert st["face_scan"]["status"] == "withdrawn" and st["show_screen_23"] is True
    assert st["face_scan"]["withdrawn_by"] == "delete_face_scan"
    bp = c.get("/v1/me/brow-profile", headers=h).json()
    assert bp["screen"] == "55f" and bp["preferred_style"] is None and bp["actions"]["begin_scan"] == "23"
    whats = {a["what"] for a in db.list_for_user("deletion_audit", uid)}
    assert {"measurements", "brow_profile"} <= whats and ("photographs" in whats) == remove
    assert DELETE("/v1/me/face-scan", {}, h).status_code == 422          # step 2 must be answered


# ================================================== M12 account deletion

def test_account_deletion_grace_and_purge():
    e, uid, h = account()
    fake_scan(uid)
    fake_look(uid)
    assert c.post("/v1/me/delete", json={"confirm": False}, headers=h).status_code == 422
    r = c.post("/v1/me/delete", json={"confirm": True}, headers=h).json()
    assert r["screen"] == "80" and r["email_sent"] is True and r["next_screen"] == "04"
    assert r["purge_at"] - time.time() > 13.9 * 86400
    assert any(m["template"] == "account_deletion" for m in db.find_all("outbox", "to", e))
    assert c.get("/v1/me", headers=h).status_code == 401                   # sessions ended
    assert P.purge_due() == [] or uid not in [p["user_id"] for p in P.purge_due()]   # nothing before day 14
    lg = c.post("/v1/auth/login", json={"email": e, "password": PW}).json()
    assert lg["deletion_cancelled"] is True                                # signing in stops it
    h2 = {"Authorization": "Bearer " + lg["access_token"]}
    c.post("/v1/me/delete", json={"confirm": True}, headers=h2)
    purged = P.purge_due(now=time.time() + 15 * 86400)
    assert uid in [p["user_id"] for p in purged]
    assert db.get("users", uid) is None and db.list_for_user("scans", uid) == []
    assert db.list_for_user("looks", uid) == []
    assert "account" in {a["what"] for a in db.list_for_user("deletion_audit", uid)}
    assert c.post("/v1/auth/login", json={"email": e, "password": PW}).status_code == 401
    assert c.post("/v1/auth/register", json={"name": "M", "email": e, "password": PW}).status_code == 201


def test_retention_sweep_is_off_until_enabled():
    _, uid, _ = account()
    sid = fake_scan(uid)
    u = db.get("users", uid)
    u["last_interaction_at"] = time.time() - 800 * 86400
    db.put("users", uid, uid, u)
    assert P.retention_sweep() == {"enabled": False, "removed": 0}
    assert db.get("scans", sid) is not None
    out = P.retention_sweep(force=True)
    assert out["enabled"] and db.get("scans", sid) is None
    assert db.get("users", uid) is not None                                 # only biometric data goes


# ============================================================== M5 library

def test_catalogue_and_library(monkeypatch):
    cat = c.get("/v1/catalogue").json()
    om = {s["id"]: s["supports_ombre"] for s in cat["styles"]}
    assert om["straight"] is False and om["micro"] is False and om["arch"] is True
    assert [f["id"] for f in cat["finishes"]] == ["full", "ombre"]
    lib = c.get("/v1/library", params={"tone": "medium", "finish": "full"}).json()
    assert lib["total"] == 24 and lib["pages"] == 6 and lib["manifest_source"] == "convention"
    p1 = c.get("/v1/library", params={"tone": "medium", "page": 1}).json()
    assert p1["screen"] == "89" and len(p1["items"]) == 4 and p1["items"][0]["style"] == "arch"
    p6 = c.get("/v1/library", params={"tone": "medium", "page": 6}).json()
    assert p6["screen"] == "94" and p6["items"][-1]["style"] == "rounded"
    img = p1["items"][0]["image"]
    assert img["path_1254"] == "v1/full/medium/ARCH_Medium_Arch_Understated_1254.webp" and img["url_1254"] is None
    ombre = c.get("/v1/library", params={"tone": "deep", "finish": "ombre"}).json()
    assert ombre["total"] == 18 and not {i["style"] for i in ombre["items"]} & {"straight", "micro"}
    one = c.get("/v1/library", params={"tone": "fair", "style": "sharp"}).json()
    assert [i["intensity"] for i in one["items"]] == ["understated", "defined", "deliberate"]
    assert c.get("/v1/library").json()["code"] == "TONE_REQUIRED"           # guest, no tone
    _, uid, h = account()
    c.put("/v1/onboarding/skin-tone-goal", json={"skin_tone": "rich", "brow_goal": "both"}, headers=h)
    assert c.get("/v1/library", headers=h).json()["tone_from"] == "brow_profile"
    monkeypatch.setattr(config, "LIBRARY_CDN_BASE", "https://cdn.example.com")
    u = c.get("/v1/library", params={"tone": "tan", "page": 1}).json()["items"][0]["image"]["url_512"]
    assert u == "https://cdn.example.com/v1/full/tan/ARCH_Tan_Arch_Understated_512.webp"
    ed = c.get("/v1/library/editorial").json()
    assert len(ed["titles"]) == 24 and ed["display_status"] == "undecided"


# ===================================================== M7 finish validation

def test_finish_rules():
    with pytest.raises(Exception) as e:
        RS.check_finish("micro", "ombre")
    assert e.value.code == "VALIDATION_ERROR" and "Micro has no Ombre" in e.value.message
    with pytest.raises(Exception) as e:
        RS.check_finish("straight", "ombre")
    assert e.value.code == "VALIDATION_ERROR"
    RS.check_finish("straight", "full")
    RS.check_finish("arch", "ombre")
    with pytest.raises(Exception):
        RS.check_finish("arch", "glitter")


# ============================================================= M9 tracing

def test_tracing_session_from_saved_look():
    _, uid, h = account()
    lid0 = fake_look(uid)
    free = c.post("/v1/tracing/sessions", json={"look_id": lid0}, headers=h).json()
    assert free["code"] == "MEMBERSHIP_REQUIRED" and free["route_to"] == "64"   # free account: gate at 36a
    member(h)
    lid = fake_look(uid, mode="reshape")
    assert c.post("/v1/tracing/sessions", json={"look_id": lid}, headers={"X-Guest": "true"}).status_code == 403
    s = c.post("/v1/tracing/sessions", json={"look_id": lid}, headers=h).json()
    sid = s["session"]["id"]
    assert s["session"]["type"] == "sculpt" and s["next_screen"] == "73" and s["stages"][0]["id"] == "75-01"
    assert "A brow pencil in Dark Brown" in s["you_will_need"]
    u = lambda body: c.patch(f"/v1/tracing/sessions/{sid}", json=body, headers=h)
    assert u({"stage": "76-01"}).status_code == 422                        # REFINE stage on SCULPT
    assert u({"mode": "refine"}).status_code == 409                        # type is fixed
    assert u({"stage": "75-03"}).json()["session"]["last_stage"] == "75-03"
    assert u({"stage": "75-01"}).status_code == 409                        # forward only
    assert u({"event": "tracking_failed"}).json()["next_screen"] == "49c"
    assert c.post(f"/v1/tracing/sessions/{sid}/complete", headers=h).status_code == 409   # not finished
    u({"stage": "75-10"})
    done = c.post(f"/v1/tracing/sessions/{sid}/complete", headers=h).json()
    assert done["screen"] == "77" and done["state"] == 2 and done["look"]["kind"] == "traced"
    traced = c.get("/v1/looks", params={"tab": "traced"}, headers=h).json()["looks"]
    assert [lk["id"] for lk in traced] == [lid]
    prev = c.get("/v1/looks", params={"tab": "previewed"}, headers=h).json()["looks"]
    assert [lk["id"] for lk in prev] == [lid0]


def test_tracing_state_1_save_and_leave():
    _, uid, h = account()
    member(h)
    user = User(uid, "Mary", False, db.get("users", uid))
    recipe = {"style": "feathered", "colour": "taupe", "intensity": "understated", "mode": "refine", "finish": "ombre"}
    sid = T.start(user, recipe)["session"]["id"]
    for st in ("76-01", "76-10"):
        c.patch(f"/v1/tracing/sessions/{sid}", json={"stage": st}, headers=h)
    done = c.post(f"/v1/tracing/sessions/{sid}/complete", headers=h).json()
    assert done["state"] == 1 and done["actions"]["looks_good"] == "20"
    saved = c.post(f"/v1/tracing/sessions/{sid}/save", json={}, headers=h).json()
    assert saved["state"] == 2 and saved["look"]["kind"] == "traced" and saved["look"]["finish"] == "ombre"
    assert saved["look"]["name"] == "Feathered · Understated · Taupe · Ombre"   # spec 37: Ombre adds its name
    sid2 = T.start(user, recipe)["session"]["id"]
    left = c.post(f"/v1/tracing/sessions/{sid2}/leave", headers=h).json()
    assert left["next_screen"] == "36" and left["session"]["status"] == "left"
    assert c.patch(f"/v1/tracing/sessions/{sid2}", json={"stage": "76-02"}, headers=h).json()["code"] == "SESSION_CLOSED"
    assert c.post("/v1/tracing/sessions", json={"scan_id": "x"}, headers=h).status_code == 422


def test_guides_49a_49b():
    _, uid, h = account()
    assert c.post("/v1/guides", data={"strokes": "{}"}, headers=h).json()["route_to"] == "64"
    member(h)
    strokes = {"left": [[[0.1, 0.2], [0.2, 0.18], [0.3, 0.2]]], "right": [[[0.7, 0.2], [0.8, 0.18]]]}
    r = c.post("/v1/guides", data={"strokes": json.dumps(strokes)},
               files={"image": ("g.png", PNG, "image/png")}, headers=h)
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["screen"] == "49b" and j["guide"]["name"].startswith("Tracing Guide · ")
    assert j["look"]["kind"] == "traced" and j["screen_49b"]["tab"] == "traced"
    assert "/guide.png?exp=" in j["guide"]["image"] and "&sig=" in j["guide"]["image"]   # F2: signed
    gid, lid = j["guide"]["id"], j["look"]["id"]
    assert c.get(f"/v1/guides/{gid}", headers=h).json()["guide"]["strokes"]["left"][0][1] == [0.2, 0.18]
    assert [lk["id"] for lk in c.get("/v1/looks", params={"tab": "traced"}, headers=h).json()["looks"]] == [lid]
    assert c.post("/v1/guides", data={"strokes": "{}"}, headers=h).status_code == 422
    assert c.post("/v1/guides", data={"strokes": "not json"}, headers=h).status_code == 422
    c.delete(f"/v1/looks/{lid}", headers=h)
    assert c.get(f"/v1/guides/{gid}", headers=h).status_code == 404       # deleting the look removes the guide


def test_my_looks_empty_is_51():
    _, uid, h = account()
    assert c.get("/v1/looks", headers=h).json()["screen"] == "51"
    fake_look(uid)
    j = c.get("/v1/looks", headers=h).json()
    assert j["screen"] == "50" and j["looks"][0]["kind"] == "previewed"
    assert j["looks"][0]["saved_line"].startswith("Saved ")


# ========================================================= with a face photo

@pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")
def test_photo_finish_before_after_and_tracing():
    import cv2
    import numpy as np
    _, uid, h = account()
    c.post("/v1/consent", json={"type": "face_scan"}, headers=h)
    with open(PHOTO, "rb") as f:
        sc = c.post("/v1/scans", files={"photo": ("f.jpg", f, "image/jpeg")}, headers=h).json()
    sid = sc["scan_id"]
    member(h)
    base = {"scan_id": sid, "style": "arch", "intensity": "deliberate", "mode": "reshape", "views": ["eyes"],
            "finish": "full"}
    full = c.post("/v1/tryon/render", json=base, headers=h).json()
    ombre = c.post("/v1/tryon/render", json={**base, "finish": "ombre"}, headers=h).json()
    assert full["finish"] == "full" and full["resolved_from"]["finish"] == "request"
    assert ombre["render_id"] != full["render_id"]
    a = cv2.imread(str(config.MEDIA_DIR / path_of(full["images"]["eyes"]))).astype(float)
    b = cv2.imread(str(config.MEDIA_DIR / path_of(ombre["images"]["eyes"]))).astype(float)
    assert np.abs(a - b).mean() > 0.05                                     # ombre really changes pixels
    bad = c.post("/v1/tryon/render", json={**base, "style": "micro", "finish": "ombre"}, headers=h).json()
    assert bad["code"] == "VALIDATION_ERROR"
    ba = c.post("/v1/tryon/before-after", json={"scan_id": sid, "style": "arch", "intensity": "defined",
                                                   "finish": "full"}, headers=h).json()
    assert ba["before"]["label"] == "BEFORE" and ba["after"]["line"] == "After: Arch"
    assert set(ba["before"]["images"]) == {"eyes", "face"} == set(ba["after"]["images"])
    assert c.get(ba["after"]["images"]["eyes"]).status_code == 200
    lk = c.post("/v1/looks", json={"scan_id": sid, "style": "arch", "intensity": "defined", "finish": "ombre"},
                headers=h).json()["look"]
    assert lk["finish"] == "ombre" and lk["kind"] == "previewed"
    s = c.post("/v1/tracing/sessions", json={"scan_id": sid, "style": "arch", "intensity": "defined",
                                             "mode": "refine", "finish": "full"}, headers=h).json()
    assert s["session"]["type"] == "refine" and s["style_measurements"]["length_ew"] > 0
    r = DELETE("/v1/me/face-scan", {"remove_photographs": True}, h).json()
    assert r["screen"] == "55d" and db.get("looks", lk["id"])["images"] is None
