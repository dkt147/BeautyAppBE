"""Final client changes (Live Brow Experience Specification, Draft 3.2):
required finish, rename / delete looks, renewal date, skin tone change on the
held scan, 22a scan held, client copy for 42 / 43 held as data."""
import os
import time
import uuid

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import config
from app.catalogue import content as C
from app.catalogue import recommend_copy as RC
from app.catalogue.measurements import load_measurements
from app.core import db
from app.main import app
from app.services.profile_service import get_profile, remember_finish, update_profile

c = TestClient(app)
PW = "a-good-password"
PHOTO = os.getenv("ARCH_TEST_PHOTO")


def account():
    e = f"fin-{uuid.uuid4().hex[:8]}@example.com"
    r = c.post("/v1/auth/register", json={"name": "Mary", "email": e, "password": PW, "confirm_password": PW})
    assert r.status_code == 201, r.text
    j = r.json()
    return j["user"]["id"], {"Authorization": "Bearer " + j["access_token"]}


def member(h):
    r = c.post("/v1/dev/grant-membership", json={"plan": "annual", "status": "trial"}, headers=h)
    assert r.status_code == 200 and r.json()["is_member"], r.text
    return r.json()


def jpg(path, w=400, h=300):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = np.full((h, w, 3), 140, np.uint8)
    cv2.circle(img, (w // 2, h // 2), 60, (60, 80, 120), -1)
    cv2.imwrite(str(path), img)


def stored_scan(uid, face_shape="heart"):
    sid = db.new_id("scan")
    d = config.MEDIA_DIR / "scans" / sid
    jpg(d / "photo.jpg", 800, 1000)
    lm = np.zeros((478, 3), np.float32)
    lm[:, 0] = 400 + np.random.default_rng(1).normal(0, 60, 478)
    lm[:, 1] = 480 + np.random.default_rng(2).normal(0, 60, 478)
    for k, i in enumerate(RC.FACE_OVAL):
        a = 2 * np.pi * k / len(RC.FACE_OVAL) - np.pi / 2
        lm[i, 0], lm[i, 1] = 400 + 220 * np.cos(a), 500 + 300 * np.sin(a)
    np.save(d / "landmarks.npy", lm)
    db.put("scans", sid, uid, {"id": sid, "user_id": uid, "created_at": time.time(),
                               "image": {"url": config.media_url(f"scans/{sid}/photo.jpg")},
                               "face_box": [180.0, 200.0, 620.0, 800.0],
                               "face_shape": {"id": face_shape}, "skin_tone_detected": {"tone": "tan"},
                               "natural_brow_colour": {"id": "dark_brown"}})
    update_profile(uid, face_shape=face_shape, last_scan_id=sid, last_scan_at=time.time())
    return sid


def a_look(uid):
    lid = db.new_id("look")
    jpg(config.MEDIA_DIR / "looks" / lid / "eyes.jpg")
    db.put("looks", lid, uid, {"id": lid, "user_id": uid, "created_at": time.time(), "scan_id": None,
                               "style": "arch", "colour": "dark_brown", "intensity": "defined", "mode": "refine",
                               "finish": "full", "name": "Arch · Defined · Dark Brown",
                               "caption": "Arch · Defined · Dark Brown", "mode_label": "REFINE MINE",
                               "images": {"eyes": config.media_url(f"looks/{lid}/eyes.jpg")}})
    return lid


# ------------------------------------------------------------------ finish

@pytest.mark.parametrize("path,body", [
    ("/v1/tryon/render", {"style": "arch", "intensity": "defined"}),
    ("/v1/tryon/intensities", {"style": "arch"}),
    ("/v1/tryon/compare", {"style": "arch", "intensities": ["defined", "deliberate"]}),
    ("/v1/tryon/before-after", {"style": "arch", "intensity": "defined"}),
    ("/v1/looks", {"style": "arch", "intensity": "defined"}),
])
def test_finish_is_required(path, body):
    uid, h = account()
    member(h)
    sid = stored_scan(uid)
    r = c.post(path, json={"scan_id": sid, **body}, headers=h)
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"
    r = c.post(path, json={"scan_id": sid, **body, "finish": "glitter"}, headers=h)
    assert r.status_code == 422


def test_ombre_rejected_for_straight_and_micro():
    uid, h = account()
    member(h)
    sid = stored_scan(uid)
    c.patch("/v1/me/brow-profile", json={"skin_tone": "medium"}, headers=h)    # gives the scan its recommendation
    for style in ("straight", "micro"):
        for path in ("/v1/tryon/render", "/v1/looks"):
            r = c.post(path, json={"scan_id": sid, "style": style, "intensity": "defined", "colour": "dark_brown",
                                   "mode": "refine", "finish": "ombre"}, headers=h)
            assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR", r.text
            assert "has no Ombre" in r.json()["detail"]
    s = c.post("/v1/tracing/sessions", json={"scan_id": sid, "style": "micro", "intensity": "defined",
                                             "finish": "ombre"}, headers=h)
    assert s.status_code == 422


def test_finish_is_remembered_and_captions():
    uid, h = account()
    remember_finish(uid, "arch", "ombre")
    remember_finish(uid, "straight", "full")           # Full-only style: her Ombre choice is kept
    assert get_profile(uid)["finish"] == "ombre"
    assert c.get("/v1/styles", headers=h).json()["remembered_finish"] == "ombre"
    remember_finish(uid, "rounded", "full")
    assert get_profile(uid)["finish"] == "full"
    assert C.look_caption("arch", "defined", "dark_brown", finish="ombre") == "Arch · Defined · Dark Brown · Ombre"
    assert C.look_caption("arch", "defined", "dark_brown") == "Arch · Defined · Dark Brown"
    assert C.caption_29("arch", "dark_brown") == "ARCH · DARK BROWN"
    assert C.caption_29("arch", "dark_brown", "ombre") == "ARCH · DARK BROWN · OMBRE"


# ------------------------------------------------------- rename and delete

def test_rename_and_delete_look():
    uid, h = account()
    lid = a_look(uid)
    r = c.patch(f"/v1/looks/{lid}", json={"name": "  Wedding  "}, headers=h)
    assert r.status_code == 200 and r.json()["look"]["name"] == "Wedding"
    assert c.get(f"/v1/looks/{lid}", headers=h).json()["look"]["name"] == "Wedding"
    assert c.patch(f"/v1/looks/{lid}", json={}, headers=h).status_code == 422
    assert c.patch(f"/v1/looks/{lid}", json={"name": "x" * 61}, headers=h).status_code == 422
    _, h2 = account()
    assert c.patch(f"/v1/looks/{lid}", json={"name": "Mine"}, headers=h2).status_code == 404
    assert c.delete(f"/v1/looks/{lid}", headers=h2).status_code == 404       # not hers
    assert c.delete(f"/v1/looks/{lid}", headers=h).json() == {"deleted": lid}
    assert c.get(f"/v1/looks/{lid}", headers=h).status_code == 404
    assert not (config.MEDIA_DIR / "looks" / lid).exists()
    assert c.delete(f"/v1/looks/{lid}", headers=h).status_code == 404


# ------------------------------------------------------------ renewal date

def test_entitlements_renewal_date():
    uid, h = account()
    e = c.get("/v1/me/entitlements", headers=h).json()
    assert e["tier"] == "free" and e["renewal_date"] is None
    assert c.get("/v1/me/entitlements", headers={"X-Guest": "true"}).json()["renewal_date"] is None
    member(h)
    e = c.get("/v1/me/entitlements", headers=h).json()
    assert e["renewal_date"] and e["renewal_date"] == e["subscription"]["access_until"]
    assert e["renewal_at"] == e["subscription"]["period_end"]
    sub = db.find_one("subscriptions", "user_id", uid) if hasattr(db, "find_one") else None
    if sub:                                               # switched off auto-renew: no next charge
        sub["will_renew"] = False
        db.put("subscriptions", sub["id"], uid, sub)
        assert c.get("/v1/me/entitlements", headers=h).json()["renewal_date"] is None


# --------------------------------------------- brow profile: 22a and skin tone

def test_scan_held_22a_and_home():
    uid, h = account()
    c.put("/v1/onboarding/skin-tone-goal", json={"skin_tone": "medium", "brow_goal": "both"}, headers=h)
    c.post("/v1/onboarding/complete", json={}, headers=h)
    home = c.get("/v1/home", headers=h).json()
    assert home["scan_held"]["has_scan"] is False and home["actions"][0]["to"] == "22"
    bp = c.get("/v1/me/brow-profile", headers=h).json()
    assert bp["has_scan"] is False and bp["last_scan_date"] is None and bp["screen"] == "55f"
    sid = stored_scan(uid)
    home = c.get("/v1/home", headers=h).json()
    assert home["scan_held"] == {"has_scan": True, "last_scan_date": home["scan_held"]["last_scan_date"],
                                 "last_scan_id": sid, "try_on_starts_at": "22a"}
    assert home["actions"][0]["to"] == "22a" and home["scan_held"]["last_scan_date"]
    bp = c.get("/v1/me/brow-profile", headers=h).json()
    assert bp["has_scan"] is True and bp["last_scan_date"] == home["scan_held"]["last_scan_date"]
    s22a = bp["screen_22a"]
    assert s22a["title"] == "Your scan is ready." and s22a["line"] == "Try a style on it now."
    assert s22a["date_line"] == f"Scanned {bp['last_scan_date']}." and s22a["cta_to"] == "29"
    assert s22a["cta"] == "CHOOSE A STYLE" and s22a["alt"] == "Scan again" and s22a["alt_to"] == "25"


def test_skin_tone_change_reruns_on_the_held_scan():
    uid, h = account()
    sid = stored_scan(uid, "heart")
    scans_before = len(db.list_for_user("scans", uid, limit=100))
    r = c.patch("/v1/me/brow-profile", json={"skin_tone": "deep"}, headers=h).json()
    assert r["skin_tone"] == "deep"
    ref = r["refreshed"]
    assert ref["rescan_needed"] is False
    assert ref["recommendation"]["recommended"]["style"] == "structured"          # Table 2, heart
    assert ref["library"]["tone"] == "deep" and ref["library"]["items"]
    assert all(i["image"] is None or "/deep/" in i["image"]["path_512"] for i in ref["library"]["items"])
    assert len(db.list_for_user("scans", uid, limit=100)) == scans_before         # no new scan
    assert db.get("scans", sid)["recommendation"]["colour"]["id"] == ref["recommendation"]["colour"]["id"]
    assert c.get("/v1/recommendations", headers=h).json()["recommendations"][0]["image"]["path_512"] \
        .startswith("v1/full/deep/")
    # 55a: the face shape she saves is the one her recommendations use
    r = c.patch("/v1/me/brow-profile", json={"face_shape": "round"}, headers=h).json()
    assert r["face_shape"]["id"] == "round"
    assert [s["style"] for s in c.get("/v1/recommendations", headers=h).json()["recommendations"]] == \
        ["sharp", "arch"]
    assert db.get("scans", sid)["recommendation"]["recommended"]["style"] == "sharp"
    assert c.patch("/v1/me/brow-profile", json={"skin_tone": "purple"}, headers=h).status_code == 422
    assert c.patch("/v1/me/brow-profile", json={"face_shape": "egg"}, headers=h).status_code == 422


# -------------------------------------------------------- copy held as data

def test_client_copy_for_all_seven_face_shapes():
    M = load_measurements()
    for fid, fs in M.face_shapes.items():
        c42, c43 = RC.screen_42(fid), RC.screen_43(fid)
        assert c42["heading_style"] == fs.recommended_style
        assert len(c42["lines"]) == 3 and len(c43["headline"]) == 3 and len(c43["body"]) == 3
        assert c43["tagline"]
    assert RC.screen_43("oval")["headline"][0] == "Your face is balanced,"
    assert RC.screen_42("oblong")["lines"][2].endswith("where a peak would add length.")
    assert C.INTENSITIES["understated"]["body"]["refine"] == \
        "Your own shape, softly filled and groomed. Still unmistakably yours."
    assert C.STYLE_APPLIED_COPY["structured"]["body_by_mode"]["refine"] == \
        "Your own shape, filled and groomed toward a structured line."


# ------------------------------------------------------------ with a photo

@pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")
def test_save_ombre_look_keeps_finish_name_and_skin_tone():
    uid, h = account()
    c.post("/v1/consent", json={"type": "face_scan"}, headers=h)
    update_profile(uid, skin_tone="medium")
    with open(PHOTO, "rb") as f:
        sid = c.post("/v1/scans", files={"photo": ("f.jpg", f, "image/jpeg")}, headers=h).json()["scan_id"]
    member(h)
    body = {"scan_id": sid, "style": "arch", "intensity": "defined", "colour": "dark_brown", "mode": "refine"}
    r = c.post("/v1/tryon/render", json={**body, "finish": "ombre", "views": ["eyes"]}, headers=h).json()
    assert r["copy"]["caption_29"] == "ARCH · DARK BROWN · OMBRE"
    assert r["copy"]["style_applied"]["body"]
    lk = c.post("/v1/looks", json={**body, "finish": "ombre"}, headers=h).json()["look"]
    assert lk["name"] == "Arch · Defined · Dark Brown · Ombre" and lk["finish"] == "ombre"
    assert lk["skin_tone"] == "medium" and "tag" not in lk
    assert get_profile(uid)["finish"] == "ombre"
