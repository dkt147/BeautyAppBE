"""Consent records (M2, Dev Notes 1.1 and 5.2).

Two types, recorded separately:
  * biometric_notice  screen 02, four boxes, before any account exists. Held
                      against the install id, then linked to the account at
                      sign-up / sign-in.
  * face_scan         screen 23, the FACE SCAN CONSENT tick. Needs an account.

Each record keeps the policy version and the time. A consent is never edited
in place: granting again writes a new record, withdrawing stamps
withdrawn_at on the live one. Status is none, granted or withdrawn.
"""
import time
from typing import Optional

from app import config
from app.core import db
from app.core.errors import ApiError

BIOMETRIC_BOXES = ["biometric_data", "privacy_policy", "terms_of_use", "age_18"]
FACE_SCAN_TEXT = "I consent to a face scan for my brow profile and AR try-on."
TYPES = ("biometric_notice", "face_scan")


def _records(user_id: Optional[str], install_id: Optional[str], ctype: str):
    rows = []
    if user_id:
        rows += [r for r in db.list_for_user("consents", user_id, limit=1000) if r.get("type") == ctype]
    if install_id:
        rows += [r for r in db.find_all("consents", "install_id", install_id)
                 if r.get("type") == ctype and not r.get("user_id")]
    return sorted(rows, key=lambda r: r.get("granted_at") or r.get("at") or 0)


def latest(user_id, install_id, ctype):
    rows = _records(user_id, install_id, ctype)
    return rows[-1] if rows else None


def status_of(rec) -> str:
    if not rec:
        return "none"
    if rec.get("withdrawn_at") or not rec.get("granted", True):
        return "withdrawn"
    return "granted"


def grant(ctype: str, user_id: Optional[str], install_id: Optional[str], boxes: dict = None,
          policy_version: Optional[str] = None) -> dict:
    if ctype not in TYPES:
        raise ApiError("VALIDATION_ERROR", f"Unknown consent type '{ctype}'.", 422)
    if ctype == "face_scan" and not user_id:
        raise ApiError("ACCOUNT_REQUIRED", "This needs an account. Create one to continue.", 403, {"route_to": "13"})
    if ctype == "biometric_notice":
        if not (user_id or install_id):
            raise ApiError("VALIDATION_ERROR", "Send the install id (X-Install-Id) before an account exists.", 422)
        boxes = boxes or {}
        missing = [b for b in BIOMETRIC_BOXES if not boxes.get(b)]
        if missing:   # screen 02: CONTINUE is enabled only when all four are ticked
            raise ApiError("VALIDATION_ERROR", "All four boxes must be ticked to continue.", 422,
                           {"details": [{"field": f"boxes.{b}", "issue": "Required"} for b in missing]})
    now = time.time()
    rid = db.new_id("cns")
    doc = {"id": rid, "type": ctype, "user_id": user_id, "install_id": install_id, "granted": True,
           "policy_version": policy_version or config.POLICY_VERSION,
           "text_version": config.CONSENT_TEXT_VERSION if ctype == "face_scan" else None,
           "text": FACE_SCAN_TEXT if ctype == "face_scan" else None,
           "boxes": {b: True for b in BIOMETRIC_BOXES} if ctype == "biometric_notice" else None,
           "granted_at": now, "withdrawn_at": None, "withdrawn_by": None}
    db.put("consents", rid, user_id, doc, created=now)
    return doc


def withdraw(ctype: str, user_id: str, by: str) -> Optional[dict]:
    rec = latest(user_id, None, ctype)
    if not rec or status_of(rec) != "granted":
        return rec
    rec["withdrawn_at"], rec["withdrawn_by"] = time.time(), by
    db.put("consents", rec["id"], user_id, rec)
    return rec


def link_install(install_id: Optional[str], user_id: str) -> int:
    """Screen 02 happens before sign-up: attach those records to the account."""
    if not install_id:
        return 0
    n = 0
    for r in db.find_all("consents", "install_id", install_id):
        if not r.get("user_id"):
            r["user_id"] = user_id
            db.put("consents", r["id"], user_id, r)
            n += 1
    return n


def _summary(rec):
    st = status_of(rec)
    outdated = bool(rec) and st == "granted" and rec.get("policy_version") != config.POLICY_VERSION
    return {"status": st, "policy_version": rec.get("policy_version") if rec else None,
            "granted_at": rec.get("granted_at") if rec else None,
            "withdrawn_at": rec.get("withdrawn_at") if rec else None,
            "withdrawn_by": rec.get("withdrawn_by") if rec else None,
            "policy_outdated": outdated}


def status(user_id: Optional[str], install_id: Optional[str]) -> dict:
    face = _summary(latest(user_id, None, "face_scan") if user_id else None)
    bio = _summary(latest(user_id, install_id, "biometric_notice"))
    show_23 = config.SCREEN_23_ENABLED and (
        face["status"] != "granted" or (config.RECONSENT_ON_POLICY_CHANGE and face["policy_outdated"]))
    show_02 = bio["status"] != "granted" or (config.RECONSENT_ON_POLICY_CHANGE and bio["policy_outdated"])
    return {"current_policy_version": config.POLICY_VERSION, "screen_23_enabled": config.SCREEN_23_ENABLED,
            "face_scan": face, "biometric_notice": bio,
            "show_screen_23": show_23, "show_screen_02": show_02}


def face_scan_ok(user_id: str) -> bool:
    """A scan may run: consent granted, or screen 23 switched off by the flag."""
    if not config.SCREEN_23_ENABLED:
        return True
    return not status(user_id, None)["show_screen_23"]
