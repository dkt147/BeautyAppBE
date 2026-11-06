"""Block 3: F2 private media, M0 dev gates, M10 membership + billing,
M8 rename / share, M11 devices, M13 support + config + rate limits,
M6 recommendations 41-43, M3 preferences, home 20."""
import base64
import datetime as dt
import hashlib
import hmac
import json
import time
import uuid

import cv2
import jwt
import numpy as np
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID, ObjectIdentifier
from fastapi.testclient import TestClient

from app import config
from app.catalogue.recommend_copy import FACE_OVAL
from app.core import db, ratelimit
from app.core.media import path_of, sign_url
from app.main import app
from app.services import billing_service as B
from app.services import notify

c = TestClient(app)
PW = "a-good-password"


def account():
    e = f"b3-{uuid.uuid4().hex[:8]}@example.com"
    r = c.post("/v1/auth/register", json={"name": "Mary", "email": e, "password": PW, "confirm_password": PW})
    assert r.status_code == 201, r.text
    j = r.json()
    return e, j["user"]["id"], {"Authorization": "Bearer " + j["access_token"]}


def jpg(path, w=400, h=300):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = np.full((h, w, 3), 140, np.uint8)
    cv2.circle(img, (w // 2, h // 2), 60, (60, 80, 120), -1)
    cv2.imwrite(str(path), img)


def real_look(uid):
    lid = db.new_id("look")
    jpg(config.MEDIA_DIR / "looks" / lid / "eyes.jpg")
    db.put("looks", lid, uid, {"id": lid, "user_id": uid, "created_at": time.time(), "scan_id": None,
                               "style": "arch", "colour": "dark_brown", "intensity": "defined", "mode": "refine",
                               "finish": "full", "name": "My Everyday Arch", "caption": "Arch · Defined · Dark Brown",
                               "mode_label": "REFINE MINE",
                               "images": {"eyes": config.media_url(f"looks/{lid}/eyes.jpg")}})
    return lid


def synthetic_scan(uid, face_shape="heart"):
    """A stored scan with plausible landmarks (no vision run)."""
    sid = db.new_id("scan")
    d = config.MEDIA_DIR / "scans" / sid
    jpg(d / "photo.jpg", 800, 1000)
    rng = np.random.default_rng(1)
    lm = np.zeros((478, 3), np.float32)
    lm[:, 0] = 400 + rng.normal(0, 60, 478)
    lm[:, 1] = 480 + rng.normal(0, 60, 478)
    for k, i in enumerate(FACE_OVAL):
        a = 2 * np.pi * k / len(FACE_OVAL) - np.pi / 2
        lm[i, 0], lm[i, 1] = 400 + 220 * np.cos(a), 500 + 300 * np.sin(a)
    np.save(d / "landmarks.npy", lm)
    db.put("scans", sid, uid, {"id": sid, "user_id": uid, "created_at": time.time(),
                               "image": {"url": config.media_url(f"scans/{sid}/photo.jpg")},
                               "face_box": [180.0, 200.0, 620.0, 800.0],
                               "face_shape": {"id": face_shape}, "skin_tone_detected": {"tone": "tan"}})
    from app.services.profile_service import update_profile
    update_profile(uid, face_shape=face_shape, last_scan_id=sid, last_scan_at=time.time())
    return sid


# ================================================================ F2 media

def test_media_is_private_and_signed():
    _, uid, h = account()
    lid = real_look(uid)
    url = c.get(f"/v1/looks/{lid}", headers=h).json()["look"]["images"]["eyes"]
    assert "?exp=" in url and "&sig=" in url                       # signed on the way out
    assert db.get("looks", lid)["images"]["eyes"].endswith("eyes.jpg")   # stored plain, never goes stale
    r = c.get(url)
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    plain = url.split("?", 1)[0]
    assert c.get(plain).json()["code"] == "MEDIA_LINK_INVALID"     # no public folder any more
    tampered = url[:-4] + ("0000" if not url.endswith("0000") else "1111")
    assert c.get(tampered).status_code == 403
    other = url.replace(lid, db.new_id("look"))
    assert c.get(other).status_code == 403                         # signature is bound to the path
    old = sign_url(config.media_url(f"looks/{lid}/eyes.jpg"), now=time.time() - 3600)
    assert c.get(old).json()["code"] == "MEDIA_LINK_EXPIRED"
    trav = sign_url(config.media_url("../arch.db"))
    assert c.get(trav).status_code in (403, 404)


# ============================================================== M0 dev gates

def test_dev_routes_off_outside_dev(monkeypatch):
    _, uid, h = account()
    monkeypatch.setattr(config, "ENV", "production")
    for method, url in [("post", "/v1/dev/run-jobs"), ("post", "/v1/dev/grant-membership"),
                        ("post", "/v1/dev/reset-test-user"), ("get", "/live"), ("get", "/v1/dev/scan-debug/x")]:
        r = getattr(c, method)(url, headers=h, **({"json": {}} if method == "post" else {}))
        assert r.status_code == 404, url


# ======================================================== M10 entitlements

def test_free_member_and_screen_data():
    _, uid, h = account()
    e = c.get("/v1/me/entitlements", headers=h).json()
    assert e["tier"] == "free" and e["can"] == {"scan": True, "tryon": True, "save_look": False,
                                                "trace": False, "guide": False}
    o = e["offer"]
    assert [p["price"] for p in o["plans"]] == ["$19.99", "$179.99"] and o["saving"] == \
        "Save $59.89 a year against paying monthly." and o["trial"] == "Start with 14 days free."
    assert c.get("/v1/me/entitlements", headers={"X-Guest": "true"}).json()["tier"] == "guest"
    looks = c.get("/v1/looks", headers=h).json()
    assert looks["screen"] == "51" and looks["membership_line"]["to"] == "64" and not looks["is_member"]
    m = c.post("/v1/dev/grant-membership", json={"plan": "annual", "status": "trial"}, headers=h).json()
    assert m["is_member"] and m["screen_67"]["plan"] == "ARCH Membership · Annual"
    assert m["screen_67"]["then"] == "$179.99 per year"
    assert c.get("/v1/me", headers=h).json()["membership"]["badge"] == "MEMBER"


def test_trial_dates_rule():
    start = dt.datetime(2026, 10, 30, 10, 0).timestamp()
    assert B.trial_dates(start) == ("12 November 2026", "13 November 2026")


def test_cancelled_keeps_access_until_period_end_then_free():
    _, uid, h = account()
    c.post("/v1/dev/grant-membership", json={"status": "cancelled", "days": 5}, headers=h)
    e = c.get("/v1/me/entitlements", headers=h).json()
    assert e["is_member"] and e["screen_72"]["further_charges"] == "None"
    c.post("/v1/dev/grant-membership", json={"status": "expired"}, headers=h)
    assert c.get("/v1/me/entitlements", headers=h).json()["tier"] == "free"


# -------------------------------------------------- Apple: real x5c chain

def _cert(subject, issuer, pub, signer, oid=None, ca=False, days=30):
    now = dt.datetime.now(dt.timezone.utc)
    b = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)]))
         .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer)])).public_key(pub)
         .serial_number(x509.random_serial_number()).not_valid_before(now - dt.timedelta(days=1))
         .not_valid_after(now + dt.timedelta(days=days))
         .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True))
    if oid:
        b = b.add_extension(x509.UnrecognizedExtension(ObjectIdentifier(oid), b"\x05\x00"), critical=False)
    return b.sign(signer, hashes.SHA256())


@pytest.fixture
def apple_chain(tmp_path, monkeypatch):
    rk, ik, lk = (ec.generate_private_key(ec.SECP256R1()) for _ in range(3))
    root = _cert("Test Apple Root CA - G3", "Test Apple Root CA - G3", rk.public_key(), rk, ca=True)
    inter = _cert("Test WWDR", "Test Apple Root CA - G3", ik.public_key(), rk, B.APPLE_INTERMEDIATE_OID, ca=True)
    leaf = _cert("Test Prod ECC Mac App Store", "Test WWDR", lk.public_key(), ik, B.APPLE_LEAF_OID)
    p = tmp_path / "root.pem"
    p.write_bytes(root.public_bytes(serialization.Encoding.PEM))
    monkeypatch.setattr(config, "APPLE_ROOT_CA_PATH", str(p))
    x5c = [base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode() for cert in (leaf, inter, root)]

    def sign(payload, key=lk):
        return jwt.encode(payload, key, algorithm="ES256", headers={"x5c": x5c})
    return sign


def _tx(orig, token=None, trial=True, days=14, **kw):
    now = int(time.time() * 1000)
    return {"originalTransactionId": orig, "transactionId": orig + "-1", "bundleId": config.APPLE_BUNDLE_ID,
            "productId": "com.cbygroyals.arch.annual", "purchaseDate": now, "expiresDate": now + days * 86400000,
            "offerType": 1 if trial else None, "offerDiscountType": "FREE_TRIAL" if trial else None,
            "appAccountToken": token, "environment": "Sandbox", **kw}


def test_apple_verify_and_notifications(apple_chain):
    e, uid, h = account()
    tok = c.get("/v1/me/entitlements", headers=h).json()["app_account_token"]
    orig = "2000" + uuid.uuid4().hex[:8]
    r = c.post("/v1/billing/apple/verify", json={"signed_transaction": apple_chain(_tx(orig, tok))}, headers=h).json()
    assert r["is_member"] and r["subscription_status"] == "trial" and r["next_screen"] == "65"
    assert r["payment_method"] == "App Store"
    assert any(m["template"] == "trial_started" for m in db.find_all("outbox", "to", e))

    def note(ntype, subtype=None, nid=None, **txkw):
        payload = {"notificationType": ntype, "subtype": subtype, "notificationUUID": nid or uuid.uuid4().hex,
                   "data": {"signedTransactionInfo": apple_chain(_tx(orig, tok, **txkw)),
                            "signedRenewalInfo": apple_chain({"autoRenewStatus": 1,
                                                              "gracePeriodExpiresDate": int((time.time() + 16 * 86400) * 1000)})}}
        return c.post("/v1/webhooks/apple", json={"signedPayload": apple_chain(payload)}).json()

    nid = uuid.uuid4().hex
    assert note("DID_FAIL_TO_RENEW", "GRACE_PERIOD", nid, trial=False)["status"] == "grace"
    assert note("DID_FAIL_TO_RENEW", "GRACE_PERIOD", nid, trial=False) == {"duplicate": True}
    ent = c.get("/v1/me/entitlements", headers=h).json()
    assert ent["is_member"] and any(f"{d} days" in ent["screen_68"]["line"] for d in (15, 16))
    assert any(m["template"] == "payment_failed" for m in db.find_all("outbox", "to", e))
    assert note("DID_CHANGE_RENEWAL_STATUS", "AUTO_RENEW_DISABLED", trial=False)["status"] == "cancelled"
    assert c.get("/v1/me/entitlements", headers=h).json()["is_member"]           # access to period end
    assert note("EXPIRED", "VOLUNTARY", trial=False)["status"] == "expired"
    assert c.get("/v1/me/entitlements", headers=h).json()["tier"] == "free"


def test_apple_rejects_forged_and_other_accounts(apple_chain):
    _, uid, h = account()
    bad_key = ec.generate_private_key(ec.SECP256R1())
    forged = apple_chain(_tx("9" + uuid.uuid4().hex[:8]), key=bad_key)            # chain ok, signature wrong
    assert c.post("/v1/billing/apple/verify", json={"signed_transaction": forged}, headers=h).json()["code"] \
        == "RECEIPT_INVALID"
    unsigned = jwt.encode(_tx("8" + uuid.uuid4().hex[:8]), "x" * 32, algorithm="HS256")
    assert c.post("/v1/billing/apple/verify", json={"signed_transaction": unsigned}, headers=h).json()["code"] \
        == "RECEIPT_INVALID"
    wrong_app = apple_chain(_tx("7" + uuid.uuid4().hex[:8], bundleId="com.other.app"))
    assert c.post("/v1/billing/apple/verify", json={"signed_transaction": wrong_app}, headers=h).status_code == 400
    _, _, h2 = account()
    tok2 = c.get("/v1/me/entitlements", headers=h2).json()["app_account_token"]
    theirs = apple_chain(_tx("6" + uuid.uuid4().hex[:8], tok2))
    assert c.post("/v1/billing/apple/verify", json={"signed_transaction": theirs}, headers=h).json()["code"] \
        == "RECEIPT_OTHER_ACCOUNT"


def test_billing_not_configured():
    _, uid, h = account()
    assert c.post("/v1/billing/apple/verify", json={"signed_transaction": "x.y.z"}, headers=h).status_code == 503
    assert c.post("/v1/billing/google/verify", json={"purchase_token": "t"}, headers=h).status_code == 503
    assert c.post("/v1/billing/web/checkout", headers=h).json()["code"] == "BILLING_NOT_CONFIGURED"
    assert c.post("/v1/webhooks/web", content=b"{}").status_code == 503
    assert c.post("/v1/webhooks/google", json={}).status_code == 401


def test_google_verify_and_rtdn(monkeypatch):
    _, uid, h = account()
    tok = c.get("/v1/me/entitlements", headers=h).json()["app_account_token"]
    exp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)).isoformat().replace("+00:00", "Z")
    state = {"s": "SUBSCRIPTION_STATE_ACTIVE"}
    monkeypatch.setattr(B, "google_fetch_subscription", lambda t: {
        "subscriptionState": state["s"], "startTime": "2026-11-01T10:00:00Z",
        "externalAccountIdentifiers": {"obfuscatedExternalAccountId": tok},
        "lineItems": [{"productId": "arch_monthly", "expiryTime": exp, "autoRenewingPlan": {"autoRenewEnabled": True}}]})
    r = c.post("/v1/billing/google/verify", json={"purchase_token": "gp-token-1"}, headers=h).json()
    assert r["is_member"] and r["subscription"]["plan"] == "monthly" and r["payment_method"] == "Google Play"
    monkeypatch.setattr(B, "verify_pubsub_token", lambda b: {"iss": "accounts.google.com"})
    state["s"] = "SUBSCRIPTION_STATE_ON_HOLD"
    data = base64.b64encode(json.dumps({"subscriptionNotification": {"purchaseToken": "gp-token-1",
                                                                     "notificationType": 5}}).encode()).decode()
    out = c.post("/v1/webhooks/google", json={"message": {"data": data, "messageId": uuid.uuid4().hex}},
                 headers={"Authorization": "Bearer x"}).json()
    assert out["status"] == "billing_retry"
    assert c.get("/v1/me/entitlements", headers=h).json()["tier"] == "free"


def test_web_webhook_contract(monkeypatch):
    _, uid, h = account()
    tok = c.get("/v1/me/entitlements", headers=h).json()["app_account_token"]
    monkeypatch.setattr(config, "WEB_WEBHOOK_SECRET", "s3cret")
    body = json.dumps({"event_id": uuid.uuid4().hex, "app_account_token": tok, "plan": "annual", "status": "active",
                       "period_end": time.time() + 86400 * 365, "card_brand": "Visa", "card_last4": "4242"}).encode()
    sig = hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
    assert c.post("/v1/webhooks/web", content=body, headers={"X-Signature": "bad"}).status_code == 401
    assert c.post("/v1/webhooks/web", content=body, headers={"X-Signature": sig}).json()["status"] == "active"
    assert c.get("/v1/me/entitlements", headers=h).json()["payment_method"] == "Visa ···· 4242"


def test_billing_jobs_reminders_once():
    e, uid, h = account()
    c.post("/v1/dev/grant-membership", json={"status": "trial", "days": 1}, headers=h)
    first = B.run_billing_jobs()
    assert first["reminders_sent"] >= 1
    sent = [m for m in db.find_all("outbox", "to", e) if m["template"] == "trial_ending"]
    assert len(sent) == 1
    B.run_billing_jobs()
    assert len([m for m in db.find_all("outbox", "to", e) if m["template"] == "trial_ending"]) == 1
    B.run_billing_jobs(now=time.time() + 2 * 86400)                       # trial over
    assert c.get("/v1/me/entitlements", headers=h).json()["tier"] == "free"


# ================================================================ M8 (50, 52)

def test_rename_and_share_image():
    _, uid, h = account()
    lid = real_look(uid)
    r = c.patch(f"/v1/looks/{lid}", json={"name": "  Evening arch  ", "tag": "occasion"}, headers=h).json()["look"]
    assert r["name"] == "Evening arch" and r["tag"] == "occasion"
    assert c.patch(f"/v1/looks/{lid}", json={"name": " "}, headers=h).status_code == 422
    assert c.patch(f"/v1/looks/{lid}", json={}, headers=h).status_code == 422
    sh = c.post(f"/v1/looks/{lid}/share-image", headers=h).json()
    assert sh["caption"] == "Evening arch" and [o["id"] for o in sh["options"]] == ["save_image", "share_message"]
    img = c.get(sh["image"])
    assert img.status_code == 200 and len(img.content) > 1000
    _, _, h2 = account()
    assert c.post(f"/v1/looks/{lid}/share-image", headers=h2).status_code == 404     # not hers
    lk = db.get("looks", lid)
    lk["images"] = None
    db.put("looks", lid, uid, lk)
    assert c.post(f"/v1/looks/{lid}/share-image", headers=h).json()["code"] == "PHOTO_REMOVED"


# ================================================================ M11 (82)

def test_devices_and_push():
    _, uid, h = account()
    d = c.post("/v1/devices", json={"platform": "ios", "push_token": "apns-" + uuid.uuid4().hex}, headers=h).json()
    assert "push_token" not in d["device"]
    lst = c.get("/v1/devices", headers=h).json()
    assert len(lst["devices"]) == 1 and lst["notification_prompt_seen"] is True
    assert len(notify.send_push(uid, "trial_ending")) == 1
    c.patch("/v1/me/preferences", json={"notifications_on": False}, headers=h)
    assert notify.send_push(uid, "trial_ending") == []                     # switch on 56 is off
    assert c.delete(f"/v1/devices/{d['device']['id']}", headers=h).json()["deleted"]
    assert c.get("/v1/devices", headers=h).json()["devices"] == []


# ===================================================== M13 support + config

def test_support_message_and_config():
    r = c.post("/v1/support/messages", json={"name": "Mary", "email": "mary@example.com",
                                             "message": "I'd like to know more about the annual membership."})
    assert r.status_code == 201 and r.json()["next_screen"] == "53"
    sent = [m for m in db.find_all("outbox", "to", config.SUPPORT_EMAIL) if m["template"] == "support_message"]
    assert sent and sent[-1]["data"]["reply_to"] == "mary@example.com"
    assert c.post("/v1/support/messages", json={"name": "M", "email": "nope", "message": "hi"}).status_code == 422
    cfg = c.get("/v1/config").json()
    assert cfg["membership"]["price_annual"] == 179.99 and cfg["membership"]["trial_days"] == 14
    assert cfg["refund_wording"]["web"] == "" and cfg["privacy_policy_url"] == "https://cbygroyals.com/privacy"
    assert len(cfg["languages"]) == 6


def test_rate_limits(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMITS_ENABLED", True)
    ratelimit.reset()
    body = {"name": "M", "email": "m@example.com", "message": "hello there"}
    codes = [c.post("/v1/support/messages", json=body).status_code for _ in range(6)]
    assert codes == [201] * 5 + [429]
    ratelimit.reset()


# =========================================================== M6 (41-43)

def test_recommendations_41_42_43():
    _, uid, h = account()
    assert c.get("/v1/recommendations", headers=h).json()["code"] == "SCAN_REQUIRED"
    assert c.get("/v1/recommendations", headers={"X-Guest": "true"}).json()["route_to"] == "13"
    synthetic_scan(uid, "heart")
    c.patch("/v1/me/brow-profile", json={"preferred_style": "feathered"}, headers=h)
    r = c.get("/v1/recommendations", headers=h).json()
    assert [s["style"] for s in r["recommendations"]] == ["structured", "rounded"]      # Table 2, heart
    assert r["recommendations"][0]["label"] == "Top recommendation" and r["avoid"] == ["bold"]
    assert r["your_pick"]["style"] == "feathered" and r["title"] == "Your face shape: Heart"
    assert r["recommendations"][0]["image"]["path_512"].startswith("v1/full/tan/")
    w = c.get("/v1/recommendations/structured", headers=h).json()
    assert w["fit"] == "suits" and len(w["screen_42"]["points"]) == 3
    assert w["screen_42"]["points"][2].startswith("Heart faces carry this shape")
    s43 = w["screen_43"]
    assert s43["title"].startswith("Your face is widest at the forehead") and s43["provisional"] is True
    assert len(s43["outline"]["points"]) == len(FACE_OVAL) and s43["outline"]["length_to_width"] > 1.2
    assert c.get(s43["outline"]["image"]).status_code == 200
    assert c.get("/v1/recommendations/bold", headers=h).json()["fit"] == "avoid"
    assert c.get("/v1/recommendations/arch", headers=h).json()["fit"] == "neutral"
    assert c.get("/v1/recommendations/nope", headers=h).status_code == 422


# ============================================================ M3 (56, 57)

def test_preferences_56_57():
    _, uid, h = account()
    p = c.get("/v1/me/preferences", headers=h).json()
    assert p["preferences"] == {"notifications_on": True, "auto_save_looks": True, "camera_auto_detect": False,
                                "language": "en-GB", "set_by_her": []}
    assert [lang["name"] for lang in p["languages"]][4] == "日本語"
    r = c.patch("/v1/me/preferences", json={"language": "fr", "camera_auto_detect": True}, headers=h).json()
    assert r["preferences"]["language"] == "fr" and r["next_screen"] == "53"
    assert r["preferences"]["set_by_her"] == ["camera_auto_detect", "language"]
    assert c.patch("/v1/me/preferences", json={"language": "xx"}, headers=h).status_code == 422
    assert c.patch("/v1/me/preferences", json={}, headers=h).status_code == 422


# ================================================================== home 20

def test_home_19_then_20():
    _, uid, h = account()
    c.put("/v1/onboarding/skin-tone-goal", json={"skin_tone": "medium", "brow_goal": "both"}, headers=h)
    c.post("/v1/onboarding/complete", json={}, headers=h)
    assert c.get("/v1/home", headers=h).json()["screen"] == "19"
    assert c.get("/v1/home", headers=h).json()["screen"] == "20"
    real_look(uid)
    home = c.get("/v1/home", headers=h).json()
    assert home["screen"] == "21" and home["last_look"]["image_url"] is None    # no face image: no crash
