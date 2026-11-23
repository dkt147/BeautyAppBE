"""TestFlight readiness, 24 November 2026: the client tests every screen,
tracing (73 to 77) above all. These pin what she will see:
- /strokes for both modes and both finishes (thin gold line data, Ombre alpha ramp);
- the Ombre render is a real gradient in the pixels (lighter head, same tail), Full is solid;
- one member journey through the backend calls of screens 12 to 94.
Scan-based tests need a face photo: set ARCH_TEST_PHOTO=path/to/face.jpg."""
import json
import uuid

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core import db
from app.main import app
from app.services.scan_service import load_scan_assets
from tests.test_final import PHOTO, member

c = TestClient(app)
PW = "a-good-password"
needs_photo = pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")


def account():
    e = f"tf-{uuid.uuid4().hex[:8]}@example.com"
    j = c.post("/v1/auth/register", json={"name": "Mary", "email": e, "password": PW, "confirm_password": PW}).json()
    return e, {"Authorization": "Bearer " + j["access_token"]}


def scan(h):
    c.post("/v1/consent", json={"type": "face_scan"}, headers=h)
    with open(PHOTO, "rb") as f:
        r = c.post("/v1/scans", files={"photo": ("f.jpg", f, "image/jpeg")}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["scan_id"]


# ------------------------------------------------------- 73 to 77: /strokes

@needs_photo
@pytest.mark.parametrize("mode", ["reshape", "refine"])
@pytest.mark.parametrize("style,finish", [("arch", "full"), ("arch", "ombre"), ("bold", "full"), ("bold", "ombre")])
def test_strokes_every_mode_and_finish(mode, style, finish):
    _, h = account()
    member(h)
    sid = scan(h)
    s = c.post("/v1/tracing/sessions", headers=h, json={"scan_id": sid, "style": style, "mode": mode,
                                                         "finish": finish, "intensity": "defined"})
    assert s.status_code == 201, s.text
    r = c.get(f"/v1/tracing/sessions/{s.json()['session']['id']}/strokes", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert (j["mode"], j["finish"], j["style"]) == (mode, finish, style)
    n = 0
    for side in ("right", "left"):
        b = j["brows"][side]
        assert set(b) == {"outline", "centre_line", "zones"}
        for p in b["outline"]:
            assert set(p) == {"x", "y", "u", "edge", "s_ew", "n_ew", "add_zone"}
            assert 0 <= p["x"] <= 1 and 0 <= p["y"] <= 1
        n += len(b["outline"])
        for z in b["zones"]:                                         # REFINE draws only these runs
            assert set(z) == {"edge", "u_from", "u_to", "kind"} and z["kind"] in ("fill", "extension")
            assert z["u_from"] <= z["u_to"]
        assert any(p["add_zone"] for p in b["outline"]) == bool(b["zones"])
        ops = [q["opacity"] for q in b["centre_line"]]
        assert all(q["thickness"] > 0 for q in b["centre_line"])
        if finish == "full":
            assert ops == [1.0] * len(ops)                          # solid
        else:
            assert ops[0] < 0.35 and ops[-1] == 1.0 and ops == sorted(ops)   # soft head -> full tail
        # Bold 1.80 EW, kept inside the face: the tail never runs past 1.80 eye widths
        assert max(p["s_ew"] for p in b["outline"]) <= 1.80 + 0.02
    assert len(j["strokes"]) == n
    assert "never a filled patch" in j["render"]["guide"]


# ------------------------------------------------------- Ombre in the render

def _darkness(img, pts):
    return [255.0 - float(img[int(y) - 2:int(y) + 3, int(x) - 2:int(x) + 3].mean()) for x, y in pts]


@needs_photo
@pytest.mark.parametrize("style", ["arch", "bold"])
def test_ombre_render_is_a_gradient_full_is_solid(style):
    _, h = account()
    sid = scan(h)
    _, _, nat = load_scan_assets(db.get("scans", sid))
    nb = nat["right"]
    ss = np.linspace(nb.head_s, nb.tail_s, 30)
    pts = nb.frame.to_image(ss, 0.5 * (nb.top(ss) + nb.bottom(ss)))
    dark = {}
    for fin in ("full", "ombre"):
        r = c.post("/v1/tryon/render", headers=h, json={"scan_id": sid, "style": style, "finish": fin,
                                                         "mode": "reshape", "intensity": "defined",
                                                         "views": ["full"]})
        assert r.status_code == 200, r.text
        url = r.json()["images"]["full"]
        path = url[url.index("/media/"):]
        img = cv2.imdecode(np.frombuffer(c.get(path).content, np.uint8), cv2.IMREAD_COLOR).astype(np.float32)
        dark[fin] = _darkness(img, pts)
    head = np.mean(dark["full"][:8]) - np.mean(dark["ombre"][:8])
    tail = np.mean(dark["full"][-8:]) - np.mean(dark["ombre"][-8:])
    assert head > 10, (head, tail)            # Ombre head clearly lighter than Full
    assert abs(tail) < 3, (head, tail)         # tail at full strength in both


# ------------------------------------------------------- screens 12 to 94

@needs_photo
def test_member_journey_screens_12_to_94():
    """Every backend call the client will hit on TestFlight answers as the
    handover says (status and the key fields the screens read)."""
    inst = {"X-Install-Id": "inst-" + uuid.uuid4().hex[:8]}

    def ok(r, want=200):
        assert r.status_code == want, r.text
        return r.json()

    r = c.post("/v1/consent", headers=inst, json={"type": "biometric_notice", "boxes": {
        "biometric_data": True, "privacy_policy": True, "terms_of_use": True, "age_18": True}})   # 02
    assert r.status_code in (200, 201), r.text
    ok(c.get("/v1/home", headers={"X-Guest": "true"}))                                 # 12
    ok(c.get("/v1/styles"))                                                             # 12a
    email, h = account()
    ok(c.get("/v1/onboarding/options", headers=h))                                     # 14
    ok(c.put("/v1/onboarding/skin-tone-goal", headers=h,
             json={"skin_tone": "medium", "undertone": "warm", "brow_goal": "colour"}))
    ok(c.post("/v1/onboarding/confirm-tone", headers=h, json={}))                      # 15
    ok(c.put("/v1/onboarding/direction", headers=h, json={"direction": "refined_natural"}))   # 16/17
    ok(c.post("/v1/onboarding/complete", headers=h, json={}))                          # 18
    assert ok(c.get("/v1/home", headers=h))["screen"] in ("19", "20", "21")
    sid = scan(h)                                                                       # 23/25
    assert ok(c.get(f"/v1/scans/{sid}", headers=h))["before_images"]                   # 27/28
    assert ok(c.get("/v1/me/brow-profile", headers=h))["has_scan"] is True             # 22a/55
    styles = ok(c.get(f"/v1/styles?scan_id={sid}", headers=h))                        # 29
    assert "remembered_finish" in styles
    ok(c.get(f"/v1/colours?scan_id={sid}", headers=h))
    for fin in ("full", "ombre"):
        j = ok(c.post("/v1/tryon/render", headers=h, json={"scan_id": sid, "style": "arch", "finish": fin}))
        assert j["images"]["face"] and j["images"]["brow"]                             # 29/30
    assert c.post("/v1/tryon/render", headers=h, json={"scan_id": sid, "style": "micro",
                                                        "finish": "ombre"}).status_code == 422
    ok(c.get("/v1/modes")); ok(c.get("/v1/intensities"))                              # 30a/31
    ok(c.post("/v1/me/flags", headers=h, json={"mode_intro_seen": True}))
    assert len(ok(c.post("/v1/tryon/intensities", headers=h,
                         json={"scan_id": sid, "style": "arch", "finish": "ombre"}))["items"]) == 3   # 31/35a
    ok(c.post("/v1/tryon/compare", headers=h, json={"scan_id": sid, "style": "arch", "finish": "full",
                                                     "intensities": ["defined", "deliberate"]}))      # 35b
    r = c.post("/v1/looks", headers=h, json={"scan_id": sid, "style": "arch", "finish": "full"})
    assert r.status_code == 403 and r.json()["route_to"] == "64"                       # 37 free -> 64
    ent = ok(c.get("/v1/me/entitlements", headers=h))                                  # 63/64
    assert ent["offer"]["products"]["apple"] and ent["app_account_token"]
    member(h)
    look = ok(c.post("/v1/looks", headers=h, json={"scan_id": sid, "style": "arch", "finish": "ombre",
                                                    "intensity": "defined"}), 201)     # 37/38
    lid = look["look"]["id"] if "look" in look else look["id"]
    ok(c.get("/v1/looks?tab=all", headers=h)); ok(c.get(f"/v1/looks/{lid}", headers=h))   # 50/36
    ok(c.patch(f"/v1/looks/{lid}", headers=h, json={"name": "Evening arch"}))
    ok(c.post(f"/v1/looks/{lid}/share-image", headers=h))                              # 52
    ok(c.get("/v1/recommendations/arch", headers=h))                                   # 42/43
    ok(c.post("/v1/tryon/before-after", headers=h, json={"scan_id": sid, "style": "arch", "finish": "full"}))  # 44
    s = ok(c.post("/v1/tracing/sessions", headers=h, json={"look_id": lid}), 201)      # 36a
    ts = s["session"]["id"]
    assert s["next_screen"] == "73"
    ok(c.get(f"/v1/tracing/sessions/{ts}/strokes", headers=h))                         # 73
    pre = "75" if s["session"]["type"] == "sculpt" else "76"
    ok(c.patch(f"/v1/tracing/sessions/{ts}", headers=h, json={"stage": pre + "-01"}))  # 75-xx / 76-xx
    ok(c.patch(f"/v1/tracing/sessions/{ts}", headers=h, json={"event": "tracking_lost"}))  # 75c
    ok(c.patch(f"/v1/tracing/sessions/{ts}", headers=h, json={"stage": pre + "-10"}))
    ok(c.post(f"/v1/tracing/sessions/{ts}/complete", headers=h))                       # 77
    r = c.post(f"/v1/tracing/sessions/{ts}/save", headers=h, json={})               # 77 SAVE LOOK
    assert r.status_code in (200, 201) and r.json()["look"]["kind"] == "traced", r.text
    s2 = ok(c.post("/v1/tracing/sessions", headers=h, json={"look_id": lid}), 201)
    ok(c.post(f"/v1/tracing/sessions/{s2['session']['id']}/leave", headers=h))         # 75d -> 36
    g = json.dumps({"left": [[[0.3, 0.3], [0.4, 0.28], [0.45, 0.3]]], "right": [[[0.55, 0.3], [0.6, 0.28]]]})
    ok(c.post("/v1/guides", headers=h, data={"strokes": g, "name": "Guide"}), 201)    # 49a/49b
    assert ok(c.get("/v1/looks?tab=traced", headers=h))
    ok(c.get("/v1/me", headers=h)); ok(c.patch("/v1/me", headers=h, json={"name": "Mary J"}))   # 53/54
    ok(c.patch("/v1/me/brow-profile", headers=h, json={"face_shape": "oval"}))         # 55a
    ok(c.get("/v1/me/preferences", headers=h))                                         # 56
    ok(c.patch("/v1/me/preferences", headers=h, json={"language": "fr"}))              # 57
    ok(c.post("/v1/support/messages", headers=h, json={"name": "Mary", "email": email, "message": "Hi there"}), 201)  # 59
    ok(c.post("/v1/devices", headers=h, json={"platform": "ios", "push_token": "token-12345678",
                                               "permission": "granted"}), 201)         # 82
    for p in range(1, 7):                                                               # 89-94
        ok(c.get(f"/v1/library?page={p}", headers=h))
    ok(c.get("/v1/library/editorial", headers=h))
    assert ok(c.request("DELETE", "/v1/me/face-scan", headers=h,
                        json={"remove_photographs": False}))["screen"] == "55e"         # 55c/55e
    assert ok(c.get("/v1/me/brow-profile", headers=h))["screen"] == "55f"
    ok(c.post("/v1/me/delete", headers=h, json={"confirm": True}))                     # 79/80
