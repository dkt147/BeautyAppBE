"""Brow profile, Delete my face scan, account deletion and retention
(M4 + M12, Dev Notes 5.1, 5.4, 5.5).

Biometric data (scans: photo, landmarks, measurements, traced brow) and the
photographs inside saved looks are stored apart, so each can be deleted on
its own. Every deletion writes a deletion_audit row (no photos, landmarks or
face shape in it).
"""
import shutil
import time
from datetime import datetime

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core import db
from app.core.errors import ApiError
from app.services import consent_service as CS
from app.services import notify
from app.services.profile_service import get_profile, update_profile

DAY = 86400


def _date(ts):
    if not ts:
        return None
    dt = datetime.fromtimestamp(ts)
    return f"{dt.day} {dt:%B %Y}"


def audit(user_id: str, what: str, trigger: str, count: int = 1, **extra):
    aid = db.new_id("aud")
    db.put("deletion_audit", aid, user_id, {"id": aid, "user_id": user_id, "what": what, "trigger": trigger,
                                            "count": count, "at": time.time(), **extra})


# ------------------------------------------------------------ brow profile (55)

def user_scans(user_id):
    return db.list_for_user("scans", user_id, limit=10000)


def brow_profile(user_id: str) -> dict:
    """Screen 55, or 55f when there is no scan. Also tells 39 which state to show."""
    p = get_profile(user_id)
    scans = user_scans(user_id)
    has_scan = bool(scans)
    M = load_measurements()
    fs = p.get("face_shape") if has_scan else None
    brow_image = None
    if has_scan:
        latest = scans[0]
        brow_image = config.media_url(f"scans/{latest['id']}/before_brow.jpg")
        if not (config.MEDIA_DIR / "scans" / latest["id"] / "before_brow.jpg").exists():
            brow_image = latest["image"]["url"]
    style = p.get("preferred_style")
    colour = p.get("preferred_colour")
    return {
        "screen": "55" if has_scan else "55f",
        "has_scan": has_scan,
        "face_shape": {"id": fs, "name": M.face_shape(fs).name} if fs else None,
        "preferred_style": {"id": style, "name": M.style(style).name} if style else None,
        "preferred_colour": {"id": colour, **C.COLOUR_BY_ID[colour]} if colour else None,
        "last_scan": {"scan_id": scans[0]["id"], "date": _date(scans[0]["created_at"])} if has_scan else None,
        "last_scan_date": _date(scans[0]["created_at"]) if has_scan else None,
        "last_scan_id": scans[0]["id"] if has_scan else None,
        "skin_tone": p.get("skin_tone"), "undertone": p.get("undertone"),
        "remembered_finish": p.get("finish"),
        "screen_22a": scan_held(scans[0]) if has_scan else None,
        "brow_image": brow_image,
        "editable": ["face_shape", "preferred_style", "preferred_colour", "skin_tone", "undertone"],
        "actions": ({"update": "55a", "scan_again": "22", "delete_face_scan": "55b"} if has_scan
                    else {"begin_scan": "23" if CS.status(user_id, None)["show_screen_23"] else "25"}),
    }


def scan_held(scan: dict) -> dict:
    """22a Scan Held: shown instead of 22 whenever she holds a scan. CHOOSE
    A STYLE goes to 29 with this scan (no 23, no new capture)."""
    from app.catalogue import recommend_copy as RC
    c = RC.screen_22a()
    return {"screen": "22a", "scan_id": scan["id"], "label": c["label"], "title": c["title"],
            "date_line": c["date_line"].format(date=_date(scan["created_at"])), "line": c["line"],
            "cta": c["cta"], "cta_to": c["cta_to"], "alt": c["alt"], "alt_to": c["alt_to"],
            "photo": _scan_photo(scan)}


def _scan_photo(scan):
    from app.services import render_service as RS
    try:
        return RS.before_images(scan).get("face")
    except Exception:                       # photo files gone: 22a still shows its words
        return None


def refresh_from_scan(user_id: str) -> dict:
    """Re-run the recommendation on the scan she already holds, after a
    change to her skin tone, face shape or preferred colour. No new scan:
    everything needed (face shape, detected tone, natural brow colour) is
    stored on the scan."""
    from app.services.scan_service import recommendation_for
    scans = user_scans(user_id)
    if not scans:
        return None
    sc = scans[0]
    p = get_profile(user_id)
    face = p.get("face_shape") or sc["face_shape"]["id"]
    rec = recommendation_for(face, p, sc.get("skin_tone_detected"), (sc.get("natural_brow_colour") or {}).get("id"))
    sc["recommendation"] = rec
    sc["recommendation_refreshed_at"] = time.time()
    db.put("scans", sc["id"], user_id, sc)
    return rec


def update_brow_profile(user_id: str, preferred_style=None, preferred_colour=None,
                        face_shape=None, skin_tone=None, undertone=None) -> dict:
    fields = {}
    if preferred_style is not None:
        if preferred_style not in C.STYLE_ORDER:
            raise ApiError("VALIDATION_ERROR", f"Unknown style '{preferred_style}'.", 422)
        fields["preferred_style"] = preferred_style
    if preferred_colour is not None:
        if preferred_colour not in C.COLOUR_BY_ID:
            raise ApiError("VALIDATION_ERROR", f"Unknown colour '{preferred_colour}'.", 422)
        fields["preferred_colour"] = preferred_colour
    if face_shape is not None:
        if face_shape not in load_measurements().face_shapes:
            raise ApiError("VALIDATION_ERROR", "Face shape must be one of: oval, round, square, heart, diamond, "
                                               "oblong, triangle.", 422)
        if not user_scans(user_id):
            raise ApiError("SCAN_REQUIRED", "Scan your face first.", 409)
        fields["face_shape"] = face_shape
    if skin_tone is not None:
        if skin_tone not in C.SKIN_TONE_BY_ID:
            raise ApiError("VALIDATION_ERROR", f"Unknown skin tone '{skin_tone}'.", 422)
        fields["skin_tone"] = skin_tone
    if undertone is not None:
        if undertone not in C.UNDERTONES:
            raise ApiError("VALIDATION_ERROR", f"Unknown undertone '{undertone}'.", 422)
        fields["undertone"] = undertone
    if not fields:
        raise ApiError("VALIDATION_ERROR", "Nothing to change.", 422)
    update_profile(user_id, **fields)
    out = brow_profile(user_id)
    if {"skin_tone", "undertone", "face_shape", "preferred_colour"} & fields.keys():
        from app.services import library_service as L
        p = get_profile(user_id)
        rec = refresh_from_scan(user_id)
        out["refreshed"] = {
            "rescan_needed": False,
            "recommendation": rec,          # null when she holds no scan
            "library": L.library(p["skin_tone"], p.get("finish") or C.BASE_FINISH, page=1)
            if p.get("skin_tone") else None,
        }
    return out


# ----------------------------------------------------- Delete my face scan (5.4)

def _remove_scans(user_id: str) -> int:
    scans = user_scans(user_id)
    for sc in scans:
        shutil.rmtree(config.MEDIA_DIR / "scans" / sc["id"], ignore_errors=True)
        db.delete("scans", sc["id"])
    return len(scans)


def _remove_look_photographs(user_id: str) -> int:
    """Removes the photographs inside saved looks but keeps each recipe."""
    n = 0
    for lk in db.list_for_user("looks", user_id, limit=10000):
        if lk.get("images"):
            shutil.rmtree(config.MEDIA_DIR / "looks" / lk["id"], ignore_errors=True)
            lk["images"], lk["photo_removed_at"] = None, time.time()
            db.put("looks", lk["id"], user_id, lk)
            n += 1
    for g in db.list_for_user("guides", user_id, limit=10000):
        if g.get("image"):
            shutil.rmtree(config.MEDIA_DIR / "guides" / g["id"], ignore_errors=True)
            g["image"], g["photo_removed_at"] = None, time.time()
            db.put("guides", g["id"], user_id, g)
            n += 1
    return n


def delete_face_scan(user_id: str, remove_photographs: bool) -> dict:
    """One call, made only after step 2 (55c) is answered. Removes the face
    measurements, the brow profile and every scan photo. Optionally removes
    the photographs in saved looks. Then withdraws face scan consent, so the
    next scan shows 23 again."""
    n_scans = _remove_scans(user_id)
    update_profile(user_id, face_shape=None, last_scan_id=None, last_scan_at=None,
                   preferred_style=None, preferred_colour=None)
    audit(user_id, "measurements", "user", n_scans)
    audit(user_id, "brow_profile", "user")
    n_photos = _remove_look_photographs(user_id) if remove_photographs else 0
    if remove_photographs:
        audit(user_id, "photographs", "user", n_photos)
    CS.withdraw("face_scan", user_id, by="delete_face_scan")
    screen = "55d" if remove_photographs else "55e"
    return {
        "screen": screen, "deleted": {"scans": n_scans, "look_photographs": n_photos},
        "title": "Your face scan is deleted.",
        "line": ("Your measurements, brow profile and the photographs in your saved looks are removed."
                 if remove_photographs else
                 "Your measurements and brow profile are removed. The photographs in your saved looks remain."),
        "stops_working": "Try-on can't run until you scan again.",
        "actions": {"scan_again": "23", "back_to_profile": "55f"},
        "routes_to_confirm": ["scan_again"],
    }


# ------------------------------------------------- account deletion (78 to 80)

def start_account_deletion(user: dict) -> dict:
    """Mark pending, purge after the grace period, end every session. Signing
    in within the grace period stops it (auth_service._cancel_pending_deletion)."""
    from app.services.auth_service import revoke_all_sessions
    now = time.time()
    purge_at = now + config.DELETION_GRACE_DAYS * DAY
    user["status"], user["purge_at"], user["deletion_requested_at"] = "pending_deletion", purge_at, now
    db.put("users", user["id"], user["id"], user)
    revoke_all_sessions(user["id"])
    audit(user["id"], "account_deletion_requested", "user", purge_at=purge_at)
    email_sent = False
    if user.get("email"):
        try:
            notify.send_email(user["email"], "account_deletion", user_id=user["id"],
                              purge_date=_date(purge_at), days=config.DELETION_GRACE_DAYS)
            email_sent = True
        except Exception:          # 5.5: if the email fails, say so; the app hides the line
            email_sent = False
    return {"screen": "80", "status": "pending_deletion", "purge_at": purge_at, "purge_date": _date(purge_at),
            "grace_days": config.DELETION_GRACE_DAYS, "email_sent": email_sent,
            "title": "Your deletion is underway.",
            "line": f"Your account will be removed after {config.DELETION_GRACE_DAYS} days. "
                    "Sign in again within that time and the deletion stops.",
            "email_line": "A confirmation has been sent to your email address." if email_sent else None,
            "subscription_note": "Deleting your account does not cancel an App Store subscription.",
            "next_screen": "04"}


def purge_account(user_id: str, trigger: str = "user") -> dict:
    """Removes everything held for the account. Audit rows are kept."""
    n_scans = _remove_scans(user_id)
    n_photos = 0
    for lk in db.list_for_user("looks", user_id, limit=100000):
        shutil.rmtree(config.MEDIA_DIR / "looks" / lk["id"], ignore_errors=True)
        db.delete("looks", lk["id"])
        n_photos += 1
    for g in db.list_for_user("guides", user_id, limit=100000):
        shutil.rmtree(config.MEDIA_DIR / "guides" / g["id"], ignore_errors=True)
        db.delete("guides", g["id"])
    for table in ("tracing_sessions", "consents", "auth_sessions", "otp_codes", "outbox", "devices"):
        for row in db.list_for_user(table, user_id, limit=100000):
            db.delete(table, row["id"])
    db.delete("profiles", user_id)
    db.delete("users", user_id)
    audit(user_id, "measurements", trigger, n_scans)
    audit(user_id, "photographs", trigger, n_photos)
    audit(user_id, "account", trigger)
    return {"user_id": user_id, "scans": n_scans, "looks": n_photos}


def purge_due(now: float = None) -> list:
    """Scheduled job: purge accounts whose grace period has ended. Nothing is
    purged before purge_at."""
    now = now or time.time()
    due = [u for u in db.find_all("users", "status", "pending_deletion") if (u.get("purge_at") or now + 1) <= now]
    return [purge_account(u["id"], "user") for u in due]


def retention_sweep(now: float = None, force: bool = False) -> dict:
    """24-month retention (5.1): facial and biometric data only. Built but
    off until the client defines last interaction (question 17)."""
    if not (config.RETENTION_SWEEP_ENABLED or force):
        return {"enabled": False, "removed": 0}
    now = now or time.time()
    cutoff = now - config.RETENTION_MONTHS * 30.44 * DAY
    removed = 0
    for row in db.conn().execute("SELECT id FROM users").fetchall():
        u = db.get("users", row["id"])
        last = u.get("last_interaction_at") or u.get("created_at") or now
        if last < cutoff and user_scans(u["id"]):
            n = _remove_scans(u["id"])
            update_profile(u["id"], face_shape=None, last_scan_id=None, last_scan_at=None)
            audit(u["id"], "measurements", "retention", n)
            removed += n
    return {"enabled": True, "removed": removed}
