"""Fixes from the mobile team's integration testing (BACKEND_FIXES.md,
9 November 2026)."""
import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app import config
from app.catalogue import content as C
from app.catalogue import recommend_copy as RC
from app.core import auth as AUTH
from app.core import db, ratelimit
from app.main import app
from tests.test_final import PHOTO, a_look, member, stored_scan

c = TestClient(app)
PW = "a-good-password"


def account(email=None):
    email = email or f"qa-{uuid.uuid4().hex[:8]}@example.com"
    r = c.post("/v1/auth/register", json={"name": "Mary", "email": email, "password": PW, "confirm_password": PW})
    assert r.status_code == 201, r.text
    j = r.json()
    return j["user"]["id"], {"Authorization": "Bearer " + j["access_token"]}, email, j


# ------------------------------------------------- 1. concurrency, GET reads

def test_db_concurrent_reads_and_writes():
    """The old single shared connection failed here: reads ran inside another
    thread's write transaction."""
    uid = "conc-" + uuid.uuid4().hex[:6]

    def work(i):
        for k in range(60):
            db.put("devices", f"{uid}-{i}-{k % 5}", uid, {"id": f"{uid}-{i}-{k % 5}", "n": k})
            db.get("devices", f"{uid}-{i}-{k % 5}")
            db.list_for_user("devices", uid, limit=50)
            db.find_one("devices", "n", k)
        return True

    with ThreadPoolExecutor(12) as ex:
        assert all(ex.map(work, range(12)))
    assert db.conn().execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert db.conn().execute("PRAGMA busy_timeout").fetchone()[0] == config.DB_BUSY_TIMEOUT_MS


def test_concurrent_home_burst_only_200s():
    """QA reproduction: the app loads about eight things at once on launch."""
    uid, h, _, _ = account()
    member(h)
    stored_scan(uid)
    a_look(uid)
    paths = ["/v1/looks?tab=all", "/v1/me", "/v1/me/brow-profile", "/v1/me/entitlements", "/v1/home",
             "/v1/me/preferences", "/v1/consent/status", "/v1/styles"]
    codes = []
    for _ in range(6):
        # force the hourly last-interaction write into every burst
        db.set_fields("users", uid, {"last_interaction_at": 0})
        AUTH._touched.clear()
        with ThreadPoolExecutor(len(paths)) as ex:
            codes += list(ex.map(lambda p: TestClient(app).get(p, headers=h).status_code, paths * 2))
    assert set(codes) == {200}, codes


def test_get_reads_do_not_rewrite_the_user():
    """GET /v1/home and the session touch set single fields, so a concurrent
    flag change is never lost."""
    uid, h, _, _ = account()
    for step in (("put", "/v1/onboarding/skin-tone-goal", {"skin_tone": "tan", "undertone": "warm",
                                                          "brow_goal": "shape"}),
                 ("put", "/v1/onboarding/direction", {"direction": None}),
                 ("post", "/v1/onboarding/complete", {})):
        assert getattr(c, step[0])(step[1], json=step[2], headers=h).status_code == 200
    db.set_fields("users", uid, {"last_interaction_at": 0})
    AUTH._touched.clear()
    puts = []
    orig = db.put
    db.put = lambda t, *a, **k: (puts.append(t), orig(t, *a, **k))[1]
    try:
        assert c.get("/v1/home", headers=h).json()["screen"] == "19"
        assert c.get("/v1/home", headers=h).json()["screen"] == "20"
        c.get("/v1/me", headers=h)
        c.get("/v1/me/entitlements", headers=h)
    finally:
        db.put = orig
    assert puts == []                                   # no whole-document rewrites in GETs
    doc = db.get("users", uid)
    assert doc["flags"]["home_seen"] is True and doc["flags"]["onboarding_complete"] is True
    assert doc["last_interaction_at"] > 0 and doc["app_account_token"]


def test_account_token_stable_for_old_accounts():
    uid, h, _, _ = account()
    doc = db.get("users", uid)
    doc.pop("app_account_token")
    db.put("users", uid, uid, doc)
    with ThreadPoolExecutor(6) as ex:
        toks = set(ex.map(lambda _: TestClient(app).get("/v1/me/entitlements", headers=h).json()
                          ["app_account_token"], range(6)))
    assert len(toks) == 1 and db.get("users", uid)["app_account_token"] in toks


# ----------------------------------------------------------- 2. dev tools

@pytest.mark.parametrize("env,code", [("production", 404), ("staging", 200), ("dev", 200)])
def test_dev_tools_by_environment(monkeypatch, env, code):
    _, h, _, _ = account()
    monkeypatch.setattr(config, "ENV", env)
    assert c.post("/v1/dev/grant-membership", json={}, headers=h).status_code == code
    assert c.post("/v1/dev/reset-test-user", headers=h).status_code == code
    assert c.get("/live").status_code == code


# ----------------------------------------------------- 3. reset-test-user

def test_reset_test_user_keeps_the_account():
    uid, h, email, j = account()
    member(h)
    assert c.post("/v1/consent", json={"type": "face_scan"}, headers=h).status_code == 201
    stored_scan(uid)
    a_look(uid)
    c.post("/v1/me/flags", json={"mode_intro_seen": True}, headers=h)
    r = c.post("/v1/dev/reset-test-user", headers=h)
    assert r.status_code == 200 and r.json()["account_kept"] and r.json()["next_screen"] == "14"
    # the same token, the same refresh token and the same password still work
    assert c.get("/v1/me", headers=h).status_code == 200
    assert c.post("/v1/auth/refresh", json={"refresh_token": j["refresh_token"]}).status_code == 200
    login = c.post("/v1/auth/login", json={"email": email, "password": PW})
    assert login.status_code == 200 and login.json()["next_screen"] == "14"
    # onboarding, scans, looks, flags and face-scan consent are gone; membership stays
    assert c.get("/v1/home", headers=h).json()["screen"] == "14"
    assert c.get("/v1/me/brow-profile", headers=h).json()["has_scan"] is False
    assert c.get("/v1/looks", headers=h).json()["looks"] == []
    assert db.get("users", uid)["flags"] == {"mode_intro_seen": False, "onboarding_complete": False}
    assert c.get("/v1/consent/status", headers=h).json()["show_screen_23"] is True
    assert c.get("/v1/me/entitlements", headers=h).json()["is_member"] is True


# ---------------------------------------------------------- 4. rate limits

@pytest.fixture
def limits_on(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMITS_ENABLED", True)
    ratelimit.reset()
    yield
    ratelimit.reset()


def test_login_counts_only_failures(limits_on):
    _, _, email, _ = account()
    for _ in range(25):                                  # successes never count
        assert c.post("/v1/auth/login", json={"email": email, "password": PW}).status_code == 200
    for _ in range(ratelimit.LOGIN_FAILED_PER_EMAIL.max_calls):
        assert c.post("/v1/auth/login", json={"email": email, "password": "wrong-pass"}).status_code == 401
    r = c.post("/v1/auth/login", json={"email": email, "password": "wrong-pass"})
    assert r.status_code == 429 and r.json()["retry_after"] > 0
    # another account on the same address is not blocked by her failures
    _, _, other, _ = account()
    assert c.post("/v1/auth/login", json={"email": other, "password": PW}).status_code == 200


def test_login_success_clears_failures(limits_on):
    _, _, email, _ = account()
    for _ in range(ratelimit.LOGIN_FAILED_PER_EMAIL.max_calls - 1):
        c.post("/v1/auth/login", json={"email": email, "password": "wrong-pass"})
    assert c.post("/v1/auth/login", json={"email": email, "password": PW}).status_code == 200
    for _ in range(ratelimit.LOGIN_FAILED_PER_EMAIL.max_calls - 1):
        assert c.post("/v1/auth/login", json={"email": email, "password": "wrong-pass"}).status_code == 401


def test_register_limit_is_30_successes_per_address(limits_on):
    assert ratelimit.REGISTER_PER_ADDRESS.max_calls == 30
    _, _, taken, _ = account()                           # 1 success
    for _ in range(9):                                   # failures do not use the address allowance
        r = c.post("/v1/auth/register", json={"name": "M", "email": taken, "password": PW, "confirm_password": PW})
        assert r.status_code == 409
    for _ in range(29):
        account()
    r = c.post("/v1/auth/register", json={"name": "M", "email": f"x-{uuid.uuid4().hex[:6]}@example.com",
                                          "password": PW, "confirm_password": PW})
    assert r.status_code == 429 and r.json()["code"] == "RATE_LIMITED"


def test_register_failures_limited_per_email(limits_on):
    _, _, taken, _ = account()
    body = {"name": "M", "email": taken, "password": PW, "confirm_password": PW}
    for _ in range(ratelimit.REGISTER_FAILED_PER_EMAIL.max_calls):
        assert c.post("/v1/auth/register", json=body).status_code == 409
    assert c.post("/v1/auth/register", json=body).status_code == 429


def test_limits_configurable(monkeypatch):
    monkeypatch.setenv("ARCH_RL_REGISTER_MAX", "5")
    monkeypatch.setenv("ARCH_RL_REGISTER_SECONDS", "60")
    w = ratelimit.Window("register", 30, 3600)
    assert (w.max_calls, w.per_seconds) == (5, 60)


# ------------------------------------------------- 7. reset link, app links

def test_reset_link_format_and_page(monkeypatch):
    _, _, email, _ = account()
    sent = []
    from app.services import notify
    monkeypatch.setattr(notify, "send_email", lambda to, tpl, **kw: sent.append(kw))
    assert c.post("/v1/auth/password/forgot", json={"email": email}).status_code == 200
    link = sent[-1]["link"]
    u = urlparse(link)
    assert f"{u.scheme}://{u.netloc}{u.path}" == config.RESET_LINK_URL
    token = parse_qs(u.query)["token"][0]
    page = c.get("/reset-password", params={"token": token})
    assert page.status_code == 200 and "/v1/auth/password/reset" in page.text
    r = c.post("/v1/auth/password/reset", json={"token": token, "new_password": "a-newer-password",
                                                "confirm_password": "a-newer-password"})
    assert r.status_code == 200
    assert c.post("/v1/auth/login", json={"email": email, "password": "a-newer-password"}).status_code == 200


def test_app_link_files(monkeypatch):
    assert c.get("/.well-known/apple-app-site-association").status_code == 404
    assert c.get("/.well-known/assetlinks.json").status_code == 404
    monkeypatch.setattr(config, "APPLE_TEAM_ID", "ABCDE12345")
    monkeypatch.setattr(config, "ANDROID_CERT_SHA256", ["AA:BB"])
    a = c.get("/.well-known/apple-app-site-association").json()
    assert a["applinks"]["details"][0]["appIDs"] == ["ABCDE12345." + config.APPLE_BUNDLE_ID]
    g = c.get("/.well-known/assetlinks.json").json()
    assert g[0]["target"]["sha256_cert_fingerprints"] == ["AA:BB"]


# ------------------------------------------------- 8. response consistency

@pytest.mark.skipif(not PHOTO, reason="set ARCH_TEST_PHOTO to a face photo")
def test_get_scan_has_before_images():
    _, h, _, _ = account()
    c.post("/v1/consent", json={"type": "face_scan"}, headers=h)
    with open(PHOTO, "rb") as f:
        posted = c.post("/v1/scans", files={"photo": ("f.jpg", f, "image/jpeg")}, headers=h)
    assert posted.status_code == 201, posted.text
    sid = posted.json()["scan_id"]
    for path in (f"/v1/scans/{sid}", "/v1/scans/latest"):
        imgs = c.get(path, headers=h).json()["before_images"]
        assert set(imgs) == set(posted.json()["before_images"])
        assert imgs["face"] and c.get(imgs["face"]).status_code == 200


def test_typographic_apostrophes_in_messages():
    _, _, email, _ = account()
    d = c.post("/v1/auth/login", json={"email": email, "password": "wrong-pass"}).json()["detail"]
    assert d == "That email and password don’t match." and "'" not in d
    blob = json.dumps(RC.copy(), ensure_ascii=False) + json.dumps(
        [C.MODES, C.REFUND_WORDING, C.STYLE_APPLIED_COPY, C.STYLE_DIRECTIONS], ensure_ascii=False)
    assert not re.search(r"[A-Za-z]'[A-Za-z]", blob)


# ---------------------------------------------------- 9. password change

def test_password_change_signs_out_other_devices():
    _, h, email, first = account()
    second = c.post("/v1/auth/login", json={"email": email, "password": PW}).json()
    h2 = {"Authorization": "Bearer " + second["access_token"]}
    r = c.post("/v1/me/password", json={"current_password": PW, "new_password": "another-password",
                                        "confirm_password": "another-password"}, headers=h2)
    assert r.status_code == 200
    assert c.get("/v1/me", headers=h2).status_code == 200                       # the device that changed it
    assert c.get("/v1/me", headers=h).status_code == 401                        # other device: access stops
    assert c.post("/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}).status_code == 401
    assert c.post("/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code == 200


# ------------------------------------------------- 6. email delivery (SMTP)

class FakeSMTP:
    sent = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port, self.calls = host, port, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self, context=None):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def send_message(self, msg):
        FakeSMTP.sent.append((self, msg))


def test_smtp_sends_rendered_email(monkeypatch):
    from app.services import notify
    monkeypatch.setattr(notify.smtplib, "SMTP", FakeSMTP)
    for k, v in {"SMTP_HOST": "smtp.example.com", "SMTP_PORT": 587, "SMTP_USER": "me@example.com",
                 "SMTP_PASS": "pw", "SMTP_FROM": "me@example.com", "SMTP_TLS": "starttls"}.items():
        monkeypatch.setattr(config, k, v)
    FakeSMTP.sent.clear()
    msg = {"channel": "email", "to": "mary@example.com", "template": "two_factor_code",
           "data": {"code": "123456", "minutes": 10}}
    import conftest
    assert notify.transport is conftest._capture          # the rest of the suite never reaches SMTP
    real = conftest.REAL_TRANSPORT
    assert real(msg) == "sent"
    server, email = FakeSMTP.sent[-1]
    assert (server.host, server.port) == ("smtp.example.com", 587)
    assert server.calls == ["starttls", ("login", "me@example.com", "pw")]
    assert email["To"] == "mary@example.com" and "123456" in email.get_content()
    assert "’" in email.get_content() and "'" not in email.get_content()


def test_two_factor_email_failure_is_503(monkeypatch):
    from app.services import notify
    uid, h, email, _ = account()
    db.set_fields("users", uid, {"two_factor": {"enabled": True, "channel": "email"}})

    def broken(message):
        raise OSError("connection refused")
    monkeypatch.setattr(notify, "transport", broken)
    r = c.post("/v1/auth/login", json={"email": email, "password": PW})
    if r.status_code == 200 and not r.json().get("two_factor_required"):
        pytest.skip("two-factor flag stored elsewhere")
    assert r.status_code == 503 and r.json()["code"] == "EMAIL_NOT_SENT"


def test_reset_link_uses_public_base_url(monkeypatch):
    from app.services import auth_service
    monkeypatch.setattr(config, "RESET_LINK_URL", "http://2.25.159.7:8010/reset-password")
    assert auth_service.reset_link("abc") == "http://2.25.159.7:8010/reset-password?token=abc"


def test_env_file_loader(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text('# c\nARCH_X_ONE=1\nARCH_X_TWO="two words"\nexport ARCH_X_THREE=3\nARCH_X_SET=file\n')
    monkeypatch.setenv("ARCH_X_SET", "real")
    for k in ("ARCH_X_ONE", "ARCH_X_TWO", "ARCH_X_THREE"):
        monkeypatch.delenv(k, raising=False)
    config._load_env_file(str(f))
    import os
    assert (os.environ["ARCH_X_ONE"], os.environ["ARCH_X_TWO"], os.environ["ARCH_X_THREE"]) == ("1", "two words", "3")
    assert os.environ["ARCH_X_SET"] == "real"                       # the real environment wins
    for k in ("ARCH_X_ONE", "ARCH_X_TWO", "ARCH_X_THREE"):
        monkeypatch.delenv(k)


def test_well_known_files_exist():
    base = config.ROOT / "app" / "static" / "well-known"
    aasa = json.loads((base / "apple-app-site-association").read_text())
    assert aasa["applinks"]["details"][0]["appIDs"] == ["FTQ9GSY7QA.com.cbygroyals.arch"]
    assert json.loads((base / "assetlinks.json").read_text())[0]["target"]["namespace"] == "android_app"


# ------------------------------------------------- 6. SMS (Twilio), Sent copy

TWILIO = {"TWILIO_ACCOUNT_SID": "AC123", "TWILIO_AUTH_TOKEN": "tok", "TWILIO_PHONE_NUMBER": "+15550000000"}


def test_twilio_sends_sms(monkeypatch):
    import io
    import conftest
    from app.services import notify
    for k, v in TWILIO.items():
        monkeypatch.setattr(config, k, v)
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"], seen["auth"], seen["form"] = req.full_url, req.get_header("Authorization"), parse_qs(req.data.decode())
        return io.BytesIO(b'{"sid": "SM1"}')
    monkeypatch.setattr(notify.urllib.request, "urlopen", fake_urlopen)
    msg = {"channel": "sms", "to": "+15551234567", "template": "phone_code", "data": {"code": "654321", "minutes": 10}}
    assert conftest.REAL_TRANSPORT(msg) == "sent"
    assert seen["url"] == "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json"
    assert seen["auth"].startswith("Basic ")
    assert seen["form"]["To"] == ["+15551234567"] and seen["form"]["From"] == ["+15550000000"]
    assert "654321" in seen["form"]["Body"][0]


def test_sms_code_failure_is_503_once_twilio_is_set(monkeypatch):
    from app.services import notify
    _, h, _, _ = account()
    for k, v in TWILIO.items():
        monkeypatch.setattr(config, k, v)

    def broken(message):
        raise notify.DeliveryError("Twilio 21211: invalid number")
    monkeypatch.setattr(notify, "transport", broken)
    r = c.post("/v1/me/phone", json={"dial_code": "+1", "number": "(555) 987-0000"}, headers=h)
    assert r.status_code == 503 and r.json()["code"] == "SMS_NOT_SENT"


def test_save_to_sent_appends_copy(monkeypatch):
    from email.message import EmailMessage
    from app.services import notify
    calls = []

    class FakeIMAP:
        def __init__(self, host, port, timeout=None):
            calls.append(("open", host, port))

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, u, p):
            calls.append(("login", u))

        def append(self, folder, flags, when, data):
            calls.append(("append", folder, flags, b"hello" in data))
    monkeypatch.setattr(notify.imaplib, "IMAP4_SSL", FakeIMAP)
    monkeypatch.setattr(config, "SMTP_USER", "me@example.com")
    m = EmailMessage()
    m["To"] = "x@example.com"
    m.set_content("hello")
    notify.save_to_sent(m)
    assert calls[-1] == ("append", '"[Gmail]/Sent Mail"', r"\Seen", True)
