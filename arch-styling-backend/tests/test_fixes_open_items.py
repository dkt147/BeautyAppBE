"""BACKEND_FIXES.md items still open in the code on 23 November 2026:
round 2 item 10 (emails after the reply), round 5 item 22 and the round 6
note (the server acknowledges every Play purchase), and scheduled jobs that
production could never run."""
import base64
import json
import threading
import time
import uuid

import pytest
from fastapi.testclient import TestClient

import conftest
from app import config
from app.core import db, jobs
from app.main import app
from app.services import billing_service as B
from app.services import notify

c = TestClient(app)
PW = "a-good-password"


def account(domain="example.com"):
    e = f"op-{uuid.uuid4().hex[:8]}@{domain}"
    j = c.post("/v1/auth/register", json={"name": "Mary", "email": e, "password": PW, "confirm_password": PW}).json()
    return e, j["user"]["id"], {"Authorization": "Bearer " + j["access_token"]}


# ------------------------------------------------ item 10: emails after the reply

def test_smtp_timeout_is_about_ten_seconds():
    assert config.SMTP_TIMEOUT == 10


def test_reset_email_is_queued_and_the_reply_does_not_wait(monkeypatch):
    e, _, _ = account()
    gate, done = threading.Event(), []

    def slow_transport(message):          # a mail server that takes "forever"
        gate.wait(5)
        done.append(message)
        return "sent"
    monkeypatch.setattr(config, "EMAIL_BACKGROUND", True)
    monkeypatch.setattr(notify, "transport", slow_transport)
    t0 = time.time()
    r = c.post("/v1/auth/password/forgot", json={"email": e})
    assert r.status_code == 200 and time.time() - t0 < 2 and not done      # answered before the send
    gate.set()
    for _ in range(50):
        if done:
            break
        time.sleep(0.05)
    assert done and done[0]["template"] == "password_reset"


def test_two_factor_code_still_sent_before_the_reply(monkeypatch):
    monkeypatch.setattr(config, "EMAIL_BACKGROUND", True)
    _, uid, _ = account()
    db.set_fields("users", uid, {"two_factor": True})
    monkeypatch.setattr(notify, "transport", lambda m: (_ for _ in ()).throw(OSError("refused")))
    email = db.get("users", uid)["email"]
    r = c.post("/v1/auth/login", json={"email": email, "password": PW})
    assert r.status_code == 503 and r.json()["code"] == "EMAIL_NOT_SENT"    # fails outright -> still 503


def test_deletion_email_queued_and_email_sent_tells_the_truth(monkeypatch):
    monkeypatch.setattr(config, "EMAIL_BACKGROUND", True)
    monkeypatch.setattr(notify, "deliverable", conftest.REAL_DELIVERABLE)
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.example.net")
    queued = []
    monkeypatch.setattr(notify._QUEUE, "submit", lambda fn, *a: queued.append(a))
    _, _, h = account("example.com")                                         # fake test domain: never sent
    r = c.post("/v1/me/delete", json={"confirm": True}, headers=h).json()
    assert r["email_sent"] is False and r["email_line"] is None
    _, _, h = account("gmail.com")
    r = c.post("/v1/me/delete", json={"confirm": True}, headers=h).json()
    assert r["email_sent"] is True and queued[-1][2] == "account_deletion"


# ------------------------------------- round 5 item 22 / round 6: Play acknowledgement

def _play(tok, ack_state="ACKNOWLEDGEMENT_STATE_PENDING"):
    exp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 30 * 86400))
    return {"subscriptionState": "SUBSCRIPTION_STATE_ACTIVE", "startTime": "2026-11-01T10:00:00Z",
            "acknowledgementState": ack_state, "externalAccountIdentifiers": {"obfuscatedExternalAccountId": tok},
            "lineItems": [{"productId": "arch_monthly", "expiryTime": exp, "autoRenewingPlan": {"autoRenewEnabled": True}}]}


def test_play_purchase_first_seen_in_a_notification_is_acknowledged(monkeypatch):
    _, uid, h = account()
    tok = c.get("/v1/me/entitlements", headers=h).json()["app_account_token"]
    acks = []
    monkeypatch.setattr(B, "google_fetch_subscription", lambda t: _play(tok))
    monkeypatch.setattr(B, "google_acknowledge", lambda p, t: acks.append(t) or "acknowledged")
    monkeypatch.setattr(B, "verify_pubsub_token", lambda b: {"iss": "accounts.google.com"})
    token = "rtdn-" + uuid.uuid4().hex
    data = base64.b64encode(json.dumps({"subscriptionNotification": {"purchaseToken": token,
                                                                     "notificationType": 4}}).encode()).decode()
    out = c.post("/v1/webhooks/google", json={"message": {"data": data, "messageId": uuid.uuid4().hex}},
                 headers={"Authorization": "Bearer x"}).json()
    assert acks == [token] and db.get("subscriptions", out["subscription_id"])["acknowledged"] is True


def test_failed_acknowledgement_is_retried_within_three_days(monkeypatch, tmp_path):
    _, uid, h = account()
    tok = c.get("/v1/me/entitlements", headers=h).json()["app_account_token"]
    monkeypatch.setattr(B, "google_fetch_subscription", lambda t: _play(tok))
    monkeypatch.setattr(B, "google_acknowledge", lambda p, t: "failed")           # Google down at verify time
    token = "gp-" + uuid.uuid4().hex
    assert c.post("/v1/billing/google/verify", json={"purchase_token": token}, headers=h).status_code == 200
    sub = db.find_one("subscriptions", "purchase_token", token)
    assert sub["acknowledged"] is False
    assert B.retry_google_acknowledgements()["skipped"]                               # no Play key: nothing to do
    monkeypatch.setattr(config, "GOOGLE_SERVICE_ACCOUNT_JSON", str(tmp_path / "sa.json"))
    monkeypatch.setattr(B, "google_acknowledge", lambda p, t: "already_acknowledged")   # counts as success
    r = B.retry_google_acknowledgements()
    assert r["acknowledged"] >= 1 and db.get("subscriptions", sub["id"])["acknowledged"] is True
    db.set_fields("subscriptions", sub["id"], {"acknowledged": False, "created_at": time.time() - 4 * 86400})
    before = B.retry_google_acknowledgements()["retried"]
    assert db.get("subscriptions", sub["id"])["acknowledged"] is False and before >= 0   # past 3 days: left alone


# ------------------------------------------------------------ scheduled jobs

def test_jobs_run_all_and_one_failure_does_not_stop_the_rest(monkeypatch):
    monkeypatch.setattr(B, "run_billing_jobs", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    out = jobs.run_all()
    assert set(out) == {"purged", "retention", "billing", "google_ack"} and "error" in out["billing"]


def test_job_loop_starts_on_production_settings_only(monkeypatch):
    monkeypatch.setattr(config, "JOBS_INTERVAL_MINUTES", 0)
    assert jobs.start() is False                                                       # dev / tests: off
    ran = threading.Event()
    monkeypatch.setattr(jobs, "run_all", lambda: ran.set() or {})
    monkeypatch.setattr(config, "JOBS_INTERVAL_MINUTES", 0.001)                        # 60 ms
    try:
        assert jobs.start() is True and ran.wait(3)
    finally:
        jobs.stop()
        jobs._thread.join(2)
