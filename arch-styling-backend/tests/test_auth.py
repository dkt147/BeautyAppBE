"""M1 accounts, F6/F7 error shape and F5 (no silent defaults, remembered mode)."""
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from app import config
from app.core import db
from app.core.errors import error_body
from app.core.security import create_token
from app.main import app
from app.routers.styling_routes import TryOnIn, _resolve
from app.core.auth import User
from app.services import auth_service as A

c = TestClient(app)
PW = "a-good-password"


def email():
    return f"m-{uuid.uuid4().hex[:8]}@example.com"


def register(e=None, pw=PW, name="Mary"):
    e = e or email()
    r = c.post("/v1/auth/register", json={"name": name, "email": e, "password": pw, "confirm_password": pw})
    assert r.status_code == 201, r.text
    return e, r.json()


def bearer(tok):
    return {"Authorization": "Bearer " + tok}


def last_sent(to, template):
    rows = [r for r in db.find_all("outbox", "to", to) if r["template"] == template]
    return sorted(rows, key=lambda r: r["at"])[-1]


# ------------------------------------------------------------ register (05-07)

def test_register_then_me():
    e, j = register()
    assert j["next_screen"] == "14" and j["is_new_account"] and j["refresh_token"]
    me = c.get("/v1/me", headers=bearer(j["access_token"])).json()
    assert me["user"]["email"] == e and me["user"]["name"] == "Mary"
    assert me["user"]["member_since"].startswith("With us since ")
    assert me["flags"]["onboarding_complete"] is False
    assert "password_hash" not in me["user"]


def test_duplicate_email_routes_to_07():
    e, _ = register()
    r = c.post("/v1/auth/register", json={"name": "M", "email": e.upper(), "password": PW, "confirm_password": PW})
    assert r.status_code == 409
    assert r.json()["code"] == "EMAIL_REGISTERED" and r.json()["route_to"] == "07"


def test_password_mismatch_is_a_field_error_for_06():
    r = c.post("/v1/auth/register", json={"name": "M", "email": email(), "password": PW, "confirm_password": "nope-nope"})
    j = r.json()
    assert r.status_code == 422 and j["code"] == "VALIDATION_ERROR" and j["route_to"] is None
    assert {"field": "confirm_password", "issue": "Passwords do not match"} in j["details"]
    bad = c.post("/v1/auth/register", json={"name": "M", "email": "mary@gmail .com", "password": PW}).json()
    assert bad["details"][0]["field"] == "email"


# --------------------------------------------------------------- sign in (08)

def test_login_and_next_screen():
    e, _ = register()
    assert c.post("/v1/auth/login", json={"email": e, "password": "wrong-password"}).json()["code"] == "INVALID_CREDENTIALS"
    j = c.post("/v1/auth/login", json={"email": e, "password": PW}).json()
    assert j["next_screen"] == "14" and j["is_new_account"] is False


def test_no_token_is_guest_and_bad_token_is_401():
    assert c.get("/v1/home").json()["screen"] == "12"
    assert c.get("/v1/me").json()["user"]["is_guest"] is True
    r = c.get("/v1/me", headers=bearer("not-a-token"))
    assert r.status_code == 401 and r.json()["code"] == "AUTH_REQUIRED" and r.json()["route_to"] == "08"
    old = create_token("usr_x", minutes=-1)
    assert c.get("/v1/me", headers=bearer(old)).status_code == 401


def test_token_from_existing_auth_service_is_accepted():
    """../app issues {"sub", "exp"} with the shared secret and no typ."""
    import jwt
    tok = jwt.encode({"sub": "65f0c0ffee0000000000abcd", "exp": int(time.time()) + 600},
                     config.JWT_SECRET, algorithm="HS256")
    me = c.get("/v1/me", headers=bearer(tok)).json()
    assert me["user"]["id"] == "65f0c0ffee0000000000abcd" and me["user"]["is_guest"] is False


def test_pending_2fa_token_cannot_call_the_api():
    _, j = register()
    pending = create_token(j["user"]["id"], "2fa_pending", minutes=5)
    assert c.get("/v1/me", headers=bearer(pending)).status_code == 401


# ----------------------------------------------------------- refresh / logout

def test_refresh_rotates_and_logout_revokes():
    _, j = register()
    r1 = c.post("/v1/auth/refresh", json={"refresh_token": j["refresh_token"]}).json()
    assert r1["access_token"] and r1["refresh_token"] != j["refresh_token"]
    assert c.post("/v1/auth/refresh", json={"refresh_token": j["refresh_token"]}).status_code == 401
    h = bearer(r1["access_token"])
    assert c.get("/v1/me", headers=h).json()["user"]["is_guest"] is False
    assert c.post("/v1/auth/logout", headers=h).json()["next_screen"] == "08"
    assert c.get("/v1/me", headers=h).status_code == 401
    assert c.post("/v1/auth/refresh", json={"refresh_token": r1["refresh_token"]}).status_code == 401


# ------------------------------------------------------------- two-factor (11)

def test_two_factor_flow_resend_wait_and_lock():
    e, j = register()
    h = bearer(j["access_token"])
    assert c.patch("/v1/me", json={"two_factor": True}, headers=h).json()["user"]["two_factor"] is True
    lg = c.post("/v1/auth/login", json={"email": e, "password": PW}).json()
    assert lg["two_factor_required"] and lg["next_screen"] == "11" and "access_token" not in lg
    pt = lg["pending_token"]
    r = c.post("/v1/auth/2fa/resend", json={"pending_token": pt})
    assert r.status_code == 429 and r.json()["code"] == "RESEND_TOO_SOON" and r.json()["retry_after"] > 0
    code = last_sent(e, "two_factor_code")["data"]["code"]
    wrong = "000000" if code != "000000" else "111111"
    bad = c.post("/v1/auth/2fa/verify", json={"pending_token": pt, "code": wrong}).json()
    assert bad["code"] == "INVALID_CODE" and bad["route_to"] == "11" and bad["attempts_left"] == 4
    ok = c.post("/v1/auth/2fa/verify", json={"pending_token": pt, "code": code}).json()
    assert ok["access_token"] and ok["next_screen"] == "14"
    # a used code cannot be replayed
    assert c.post("/v1/auth/2fa/verify", json={"pending_token": pt, "code": code}).json()["code"] == "CODE_EXPIRED"


def test_code_locks_after_five_wrong_tries():
    _, j = register()
    uid = j["user"]["id"]
    A.issue_code(uid, "phone", "sms", "+15550001111", "phone_code", phone="+15550001111")
    real = last_sent("+15550001111", "phone_code")["data"]["code"]
    wrong = "000000" if real != "000000" else "111111"
    for _ in range(5):
        with pytest.raises(Exception):
            A.check_code(uid, "phone", wrong)
    r = c.post("/v1/me/phone/verify", json={"code": real}, headers=bearer(j["access_token"]))
    assert r.status_code == 429 and r.json()["code"] == "CODE_LOCKED"


# ------------------------------------------------------- password (09, 10, reset)

def test_forgot_and_reset_password():
    e, j = register()
    r = c.post("/v1/auth/password/forgot", json={"email": e}).json()
    assert r == {"sent_to": e, "next_screen": "10"}
    unknown = c.post("/v1/auth/password/forgot", json={"email": email()}).json()
    assert unknown["next_screen"] == "10"            # same answer, reveals nothing
    link = last_sent(e, "password_reset")["data"]["link"]
    token = link.split("token=", 1)[1]
    bad = c.post("/v1/auth/password/reset", json={"token": "nope", "new_password": "another-password"}).json()
    assert bad["code"] == "RESET_LINK_INVALID" and bad["route_to"] == "09"
    ok = c.post("/v1/auth/password/reset", json={"token": token, "new_password": "another-password",
                                                 "confirm_password": "another-password"}).json()
    assert ok["next_screen"] == "08"
    assert c.get("/v1/me", headers=bearer(j["access_token"])).status_code == 401   # old sessions end
    assert c.post("/v1/auth/password/reset", json={"token": token, "new_password": "third-password"}).status_code == 400
    assert c.post("/v1/auth/login", json={"email": e, "password": "another-password"}).status_code == 200


def test_change_password_keeps_this_session():
    e, j = register()
    h = bearer(j["access_token"])
    bad = c.post("/v1/me/password", json={"current_password": "wrong-one", "new_password": "new-password-1"}, headers=h)
    assert bad.status_code == 401
    assert c.post("/v1/me/password", json={"current_password": PW, "new_password": "new-password-1",
                                           "confirm_password": "new-password-1"}, headers=h).json()["password_changed"]
    assert c.get("/v1/me", headers=h).status_code == 200
    assert c.post("/v1/auth/login", json={"email": e, "password": "new-password-1"}).status_code == 200


# ---------------------------------------------------------------- me (54) + 65

def test_patch_me_name_and_email():
    e, j = register()
    h = bearer(j["access_token"])
    assert c.patch("/v1/me", json={"name": "Mary Johnson"}, headers=h).json()["user"]["name"] == "Mary Johnson"
    assert c.patch("/v1/me", json={"email": email()}, headers=h).json()["code"] == "INVALID_CREDENTIALS"
    taken, _ = register()
    r = c.patch("/v1/me", json={"email": taken, "current_password": PW}, headers=h).json()
    assert r["code"] == "EMAIL_REGISTERED" and r["route_to"] is None       # stay on 54
    new = email()
    assert c.patch("/v1/me", json={"email": new, "current_password": PW}, headers=h).json()["user"]["email"] == new
    assert c.patch("/v1/me", json={}, headers=h).status_code == 422
    assert c.patch("/v1/me", json={"name": "X"}, headers={"X-Guest": "true"}).json()["route_to"] == "13a"


def test_phone_number_screen_65():
    _, j = register()
    h = bearer(j["access_token"])
    sent = c.post("/v1/me/phone", json={"dial_code": "+1", "number": "(555) 123-4821"}, headers=h).json()
    assert sent["sent_to"] == "···· 4821" and sent["channel"] == "sms"
    code = last_sent("+15551234821", "phone_code")["data"]["code"]
    done = c.post("/v1/me/phone/verify", json={"code": code}, headers=h).json()
    assert done["next_screen"] == "67" and done["user"]["phone_verified"] and done["user"]["phone"] == "+15551234821"


# ------------------------------------------------------------- Apple / Google

def test_social_not_configured():
    r = c.post("/v1/auth/apple", json={"id_token": "x"})
    assert r.status_code == 503 and r.json()["code"] == "SOCIAL_NOT_CONFIGURED"


def test_social_sign_in_creates_then_links(monkeypatch):
    e, _ = register()
    claims = {"sub": "g-" + uuid.uuid4().hex[:6], "email": e, "email_verified": True, "iss": "accounts.google.com"}
    monkeypatch.setattr(A, "verify_social_token", lambda provider, tok: claims)
    j = c.post("/v1/auth/google", json={"id_token": "t"}).json()
    assert j["is_new_account"] is False and j["user"]["email"] == e          # linked by verified email
    assert set(j["user"]["sign_in_methods"]) == {"password", "google"}
    claims2 = {"sub": "a-" + uuid.uuid4().hex[:6], "email": email(), "email_verified": "true"}
    monkeypatch.setattr(A, "verify_social_token", lambda provider, tok: claims2)
    j2 = c.post("/v1/auth/apple", json={"id_token": "t", "name": "Ana"}).json()
    assert j2["is_new_account"] and j2["next_screen"] == "14" and j2["user"]["name"] == "Ana"


def test_sign_in_cancels_pending_deletion():
    e, j = register()
    doc = db.get("users", j["user"]["id"])
    doc.update(status="pending_deletion", purge_at=time.time() + 86400)
    db.put("users", doc["id"], doc["id"], doc)
    lg = c.post("/v1/auth/login", json={"email": e, "password": PW}).json()
    assert lg["deletion_cancelled"] is True and db.get("users", doc["id"])["status"] == "active"


# -------------------------------------------------------------- F6 / F7 shape

def test_error_shape_and_generic_route():
    assert error_body("SERVER_ERROR", "x", 500)["route_to"] == "88"
    assert error_body("SOMETHING_NEW", "x", 503)["route_to"] == "88"
    assert error_body("SOMETHING_NEW", "x", 400)["route_to"] is None
    r = c.get("/v1/no-such-route").json()
    assert set(r) >= {"detail", "code", "route_to"} and r["code"] == "NOT_FOUND"


# ------------------------------------------------------- F5 defaults and mode

def _scan(intensity=None):
    return {"recommendation": {"colour": {"id": "taupe"}, "intensity": intensity}}


def test_no_silent_defaults_and_remembered_mode():
    _, j = register()
    uid = j["user"]["id"]
    user = User(uid, "Mary", False, db.get("users", uid))
    h = bearer(j["access_token"])
    modes = c.get("/v1/modes", headers=h).json()
    assert modes["current"] == "refine" and modes["remembered"] is None      # starts as Refine mine
    assert c.get("/v1/modes", headers={"X-Guest": "true"}).json()["current"] is None
    assert c.get("/v1/colours").json()["default"] is None                    # no colour nobody set
    cfg = c.get("/v1/config").json()
    assert cfg["starting_mode"] == "refine" and "default_colour" not in cfg

    with pytest.raises(Exception) as e:                                       # no intensity anywhere
        _resolve(user, _scan(), TryOnIn(scan_id="s", style="arch"))
    assert e.value.code == "INTENSITY_REQUIRED"

    v, src = _resolve(user, _scan("understated"), TryOnIn(scan_id="s", style="arch"))
    assert v == {"colour": "taupe", "mode": "refine", "intensity": "understated"}
    assert src == {"colour": "scan_recommendation", "mode": "starting_mode", "intensity": "style_direction"}

    _resolve(user, _scan(), TryOnIn(scan_id="s", style="arch", mode="reshape", intensity="defined"))
    v, src = _resolve(user, _scan(), TryOnIn(scan_id="s", style="arch", intensity="defined"))
    assert v["mode"] == "reshape" and src["mode"] == "remembered"           # the toggle is remembered
    assert c.get("/v1/modes", headers=h).json()["remembered"] == "reshape"


def test_direction_sets_the_opening_mode():
    _, j = register()
    h = bearer(j["access_token"])
    c.put("/v1/onboarding/direction", json={"direction": "precise_defined"}, headers=h)
    assert c.get("/v1/modes", headers=h).json()["current"] == "reshape"
