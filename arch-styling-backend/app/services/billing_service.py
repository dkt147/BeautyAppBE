"""Membership, billing and entitlements (M10).

Tiers (build plan M10):
  guest   browse
  free    browse, scan, recommendations, eight styles, try-on, intensity, compare
  member  + save looks, trace, hand-drawn guides

Subscription states: trial, active, grace, billing_retry, cancelled (access
to period end), expired. Store events drive changes; the app never sets them.
Receipts are checked on the server so the gate cannot be bypassed:
  * Apple: signed transactions and App Store Server Notifications v2 are JWS
    signed with an x5c chain. The chain is verified up to Apple Root CA - G3
    (ARCH_APPLE_ROOT_CA_PATH) before anything changes.
  * Google: the purchase token is looked up with the Play Developer API
    (service account), and Pub/Sub pushes carry a Google-signed OIDC token.
  * Web (66, 69): provider not chosen yet. A signed webhook contract is ready.
"""
import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app import config
from app.core import db
from app.core.errors import ApiError
from app.services import notify

MEMBER_STATES = {"trial", "active", "grace"}
FREE_ACTIONS = {"browse", "account", "scan", "tryon", "recommend"}
MEMBER_ACTIONS = FREE_ACTIONS | {"save_look", "trace", "guide"}
DAY = 86400
APPLE_LEAF_OID = "1.2.840.113635.100.6.11.1"
APPLE_INTERMEDIATE_OID = "1.2.840.113635.100.6.2.1"


def _date(ts):
    if not ts:
        return None
    dt = datetime.fromtimestamp(ts)
    return f"{dt.day} {dt:%B %Y}"


def money(v):
    return f"${v:,.2f}"


# ------------------------------------------------------------ subscriptions

def current(user_id: str):
    """Her most relevant subscription: one that gives access, else the latest."""
    subs = db.list_for_user("subscriptions", user_id, limit=50)
    live = [s for s in subs if has_access(s)]
    return (live or subs or [None])[0]


def has_access(sub, now=None) -> bool:
    if not sub:
        return False
    now = now or time.time()
    st = sub["status"]
    if st in ("trial", "active"):
        return (sub.get("period_end") or now + 1) > now
    if st == "grace":
        return (sub.get("grace_until") or sub.get("period_end") or now + 1) > now
    if st == "cancelled":
        return (sub.get("period_end") or 0) > now
    return False


def tier(user) -> str:
    if user.is_guest:
        return "guest"
    return "member" if has_access(current(user.id)) else "free"


def can(user, action: str) -> bool:
    t = tier(user)
    if t == "guest":
        return action == "browse"
    return action in (MEMBER_ACTIONS if t == "member" else FREE_ACTIONS)


def app_account_token(user) -> str:
    """UUID the app passes to StoreKit (appAccountToken) / Play
    (obfuscatedAccountId), so store events find her account."""
    tok = user.doc.get("app_account_token")
    if not tok:
        tok = str(uuid.uuid4())
        user.doc["app_account_token"] = tok
        db.put("users", user.id, user.id, user.doc)
    return tok


def _user_by_account_token(tok):
    return db.find_one("users", "app_account_token", tok) if tok else None


def upsert(platform, original_id, user_id, **fields) -> dict:
    sid = f"{platform}:{original_id}"
    sub = db.get("subscriptions", sid) or {"id": sid, "platform": platform, "original_transaction_id": original_id,
                                           "created_at": time.time(), "reminders_sent": [], "user_id": user_id}
    prev = sub.get("status")
    if user_id:
        sub["user_id"] = user_id
    sub.update({k: v for k, v in fields.items() if v is not None or k in ("grace_until",)})
    sub["updated_at"] = time.time()
    db.put("subscriptions", sid, sub["user_id"], sub)
    if prev != sub["status"]:
        _on_status_change(sub, prev)
    return sub


def record_event(source, event_id, sub_id, payload) -> bool:
    """Store every billing event once. Returns False for a duplicate."""
    eid = f"{source}:{event_id}"
    if db.get("billing_events", eid):
        return False
    db.put("billing_events", eid, None, {"id": eid, "source": source, "subscription_id": sub_id,
                                         "payload": payload, "processed_at": time.time()})
    return True


def _on_status_change(sub, prev):
    """Emails ARCH sends (Dev Notes 6). App Store users get no amounts or card digits."""
    user = db.get("users", sub["user_id"]) if sub.get("user_id") else None
    if not user or not user.get("email"):
        return
    st = sub["status"]
    tmpl = {"trial": "trial_started", "grace": "payment_failed", "cancelled": "membership_cancelled"}.get(st)
    if st == "active" and prev in (None, "expired") and sub["platform"] == "web":
        tmpl = "payment_confirmed"
    if tmpl:
        notify.send_email(user["email"], tmpl, user_id=user["id"], plan=config.PLAN_NAMES.get(sub.get("plan")),
                          period_end=_date(sub.get("period_end")), platform=sub["platform"])
        if tmpl in ("payment_failed",):
            notify.send_push(user["id"], tmpl)


# ------------------------------------------------------------ Apple (JWS)

def _apple_root():
    if not config.APPLE_ROOT_CA_PATH:
        raise ApiError("BILLING_NOT_CONFIGURED", "App Store billing is not set up yet.", 503, {"route_to": None})
    from cryptography import x509
    with open(config.APPLE_ROOT_CA_PATH, "rb") as f:
        data = f.read()
    return x509.load_pem_x509_certificate(data) if b"BEGIN" in data else x509.load_der_x509_certificate(data)


def verify_apple_jws(token: str) -> dict:
    """Verify an App Store JWS (transaction, renewal info or notification):
    the x5c chain must end at Apple Root CA - G3, each certificate must sign
    the next and be in date, the Apple marker OIDs must be present, and the
    leaf key must verify the ES256 signature."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    root = _apple_root()
    bad = ApiError("RECEIPT_INVALID", "The purchase could not be confirmed.", 400)
    try:
        header = jwt.get_unverified_header(token)
        chain = [x509.load_der_x509_certificate(base64.b64decode(c)) for c in header.get("x5c", [])]
    except Exception:
        raise bad
    if header.get("alg") != "ES256" or len(chain) < 3:
        raise bad
    if chain[-1].fingerprint(hashes.SHA256()) != root.fingerprint(hashes.SHA256()):
        raise bad
    now = datetime.now(timezone.utc)
    try:
        for child, parent in zip(chain, chain[1:]):
            child.verify_directly_issued_by(parent)
        for c in chain:
            if not (c.not_valid_before_utc <= now <= c.not_valid_after_utc):
                raise ValueError("certificate out of date")
        oids = lambda c: {e.oid.dotted_string for e in c.extensions}
        if APPLE_LEAF_OID not in oids(chain[0]) or APPLE_INTERMEDIATE_OID not in oids(chain[1]):
            raise ValueError("not an App Store certificate")
        return jwt.decode(token, chain[0].public_key(), algorithms=["ES256"],
                          options={"verify_aud": False, "verify_exp": False})
    except ApiError:
        raise
    except Exception:
        raise bad


def _apple_tx_fields(tx: dict) -> dict:
    if tx.get("bundleId") and tx["bundleId"] != config.APPLE_BUNDLE_ID:
        raise ApiError("RECEIPT_INVALID", "The purchase is for a different app.", 400)
    plan = config.APPLE_PRODUCTS.get(tx.get("productId"))
    if not plan:
        raise ApiError("RECEIPT_INVALID", "Unknown product.", 400)
    exp = (tx.get("expiresDate") or 0) / 1000
    start = (tx.get("purchaseDate") or tx.get("originalPurchaseDate") or 0) / 1000
    is_trial = tx.get("offerDiscountType") == "FREE_TRIAL" or tx.get("offerType") == 1
    if tx.get("revocationDate"):
        status = "expired"
    elif exp > time.time():
        status = "trial" if is_trial else "active"
    else:
        status = "expired"
    return {"plan": plan, "product_id": tx.get("productId"), "status": status, "period_end": exp or None,
            "trial_start": start if is_trial else None, "trial_end": exp if is_trial else None,
            "environment": tx.get("environment"), "will_renew": True}


def apple_verify(user, signed_transaction: str) -> dict:
    tx = verify_apple_jws(signed_transaction)
    tok = tx.get("appAccountToken")
    if tok and tok != app_account_token(user):
        owner = _user_by_account_token(tok)
        if owner and owner["id"] != user.id:
            raise ApiError("RECEIPT_OTHER_ACCOUNT", "This purchase belongs to another ARCH account.", 409)
    sub = upsert("apple", tx["originalTransactionId"], user.id, **_apple_tx_fields(tx))
    record_event("apple_verify", tx.get("transactionId") or uuid.uuid4().hex, sub["id"], tx)
    return sub


def apple_notification(signed_payload: str) -> dict:
    """App Store Server Notifications v2."""
    n = verify_apple_jws(signed_payload)
    data = n.get("data") or {}
    tx = verify_apple_jws(data["signedTransactionInfo"]) if data.get("signedTransactionInfo") else {}
    renewal = verify_apple_jws(data["signedRenewalInfo"]) if data.get("signedRenewalInfo") else {}
    if not tx:
        return {"ignored": True}
    sid = f"apple:{tx['originalTransactionId']}"
    if not record_event("apple", n.get("notificationUUID") or uuid.uuid4().hex, sid, n):
        return {"duplicate": True}
    existing = db.get("subscriptions", sid)
    owner = (existing or {}).get("user_id") or (_user_by_account_token(tx.get("appAccountToken")) or {}).get("id")
    fields = _apple_tx_fields(tx)
    ntype, sub = n.get("notificationType"), n.get("subtype")
    if ntype == "DID_CHANGE_RENEWAL_STATUS":
        fields["will_renew"] = sub != "AUTO_RENEW_DISABLED"
        if sub == "AUTO_RENEW_DISABLED" and fields["status"] in ("trial", "active"):
            fields["status"] = "cancelled"
    elif ntype == "DID_FAIL_TO_RENEW":
        if sub == "GRACE_PERIOD":
            fields["status"] = "grace"
            fields["grace_until"] = (renewal.get("gracePeriodExpiresDate") or 0) / 1000 or \
                time.time() + config.GRACE_DAYS * DAY
        else:
            fields["status"] = "billing_retry"
    elif ntype == "GRACE_PERIOD_EXPIRED":
        fields["status"] = "billing_retry"
    elif ntype in ("EXPIRED", "REFUND", "REVOKE"):
        fields["status"] = "expired"
        fields["will_renew"] = False
    if renewal and "autoRenewStatus" in renewal and ntype != "DID_CHANGE_RENEWAL_STATUS":
        fields["will_renew"] = renewal["autoRenewStatus"] == 1
    out = upsert("apple", tx["originalTransactionId"], owner, **fields)
    return {"subscription_id": out["id"], "status": out["status"], "notification": ntype}


# ------------------------------------------------------------ Google Play

def _google_access_token() -> str:
    if not config.GOOGLE_SERVICE_ACCOUNT_JSON:
        raise ApiError("BILLING_NOT_CONFIGURED", "Google Play billing is not set up yet.", 503, {"route_to": None})
    import httpx
    with open(config.GOOGLE_SERVICE_ACCOUNT_JSON, encoding="utf-8") as f:
        sa = json.load(f)
    now = int(time.time())
    assertion = jwt.encode({"iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/androidpublisher",
                            "aud": sa.get("token_uri", "https://oauth2.googleapis.com/token"),
                            "iat": now, "exp": now + 3600}, sa["private_key"], algorithm="RS256")
    r = httpx.post(sa.get("token_uri", "https://oauth2.googleapis.com/token"), timeout=15,
                   data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion})
    r.raise_for_status()
    return r.json()["access_token"]


def google_fetch_subscription(purchase_token: str) -> dict:
    """purchases.subscriptionsv2.get"""
    import httpx
    tok = _google_access_token()
    url = (f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
           f"{config.GOOGLE_PACKAGE_NAME}/purchases/subscriptionsv2/tokens/{purchase_token}")
    r = httpx.get(url, headers={"Authorization": f"Bearer {tok}"}, timeout=15)
    if r.status_code in (400, 404, 410):
        raise ApiError("RECEIPT_INVALID", "The purchase could not be confirmed.", 400)
    r.raise_for_status()
    return r.json()


GOOGLE_STATES = {"SUBSCRIPTION_STATE_ACTIVE": "active", "SUBSCRIPTION_STATE_IN_GRACE_PERIOD": "grace",
                 "SUBSCRIPTION_STATE_ON_HOLD": "billing_retry", "SUBSCRIPTION_STATE_CANCELED": "cancelled",
                 "SUBSCRIPTION_STATE_EXPIRED": "expired", "SUBSCRIPTION_STATE_PAUSED": "expired",
                 "SUBSCRIPTION_STATE_PENDING": "expired"}


def _parse_rfc3339(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def _google_fields(p: dict) -> dict:
    items = p.get("lineItems") or [{}]
    li = items[0]
    plan = config.GOOGLE_PRODUCTS.get(li.get("productId"))
    if not plan:
        raise ApiError("RECEIPT_INVALID", "Unknown product.", 400)
    status = GOOGLE_STATES.get(p.get("subscriptionState"), "expired")
    exp = _parse_rfc3339(li.get("expiryTime"))
    is_trial = bool((li.get("offerPhase") or {}).get("freeTrial"))
    if status == "active" and is_trial:
        status = "trial"
    start = _parse_rfc3339(p.get("startTime"))
    return {"plan": plan, "product_id": li.get("productId"), "status": status, "period_end": exp,
            "trial_start": start if is_trial else None, "trial_end": exp if is_trial else None,
            "will_renew": bool((li.get("autoRenewingPlan") or {}).get("autoRenewEnabled", status != "cancelled")),
            "grace_until": exp + config.GRACE_DAYS * DAY if status == "grace" and exp else None}


def google_verify(user, purchase_token: str) -> dict:
    p = google_fetch_subscription(purchase_token)
    acct = (p.get("externalAccountIdentifiers") or {}).get("obfuscatedExternalAccountId")
    if acct and acct != app_account_token(user):
        owner = _user_by_account_token(acct)
        if owner and owner["id"] != user.id:
            raise ApiError("RECEIPT_OTHER_ACCOUNT", "This purchase belongs to another ARCH account.", 409)
    key = p.get("linkedPurchaseToken") or purchase_token
    sub = upsert("google", hashlib.sha256(key.encode()).hexdigest()[:32], user.id,
                 purchase_token=purchase_token, **_google_fields(p))
    record_event("google_verify", hashlib.sha256(purchase_token.encode()).hexdigest()[:24] + f":{int(time.time())}",
                 sub["id"], {"state": p.get("subscriptionState")})
    return sub


def verify_pubsub_token(bearer: str):
    if not config.GOOGLE_PUBSUB_AUDIENCE:
        raise ApiError("BILLING_NOT_CONFIGURED", "Google Play notifications are not set up yet.", 503,
                       {"route_to": None})
    try:
        key = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs").get_signing_key_from_jwt(bearer).key
        claims = jwt.decode(bearer, key, algorithms=["RS256"], audience=config.GOOGLE_PUBSUB_AUDIENCE)
    except Exception:
        raise ApiError("WEBHOOK_UNAUTHORISED", "Unauthorised.", 401, {"route_to": None})
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ApiError("WEBHOOK_UNAUTHORISED", "Unauthorised.", 401, {"route_to": None})
    return claims


def google_notification(body: dict) -> dict:
    msg = body.get("message") or {}
    data = json.loads(base64.b64decode(msg.get("data") or "e30=").decode() or "{}")
    sn = data.get("subscriptionNotification")
    if not sn:
        return {"ignored": True}
    if not record_event("google", msg.get("messageId") or uuid.uuid4().hex, None, data):
        return {"duplicate": True}
    token = sn["purchaseToken"]
    p = google_fetch_subscription(token)
    key = p.get("linkedPurchaseToken") or token
    sid = hashlib.sha256(key.encode()).hexdigest()[:32]
    existing = db.get("subscriptions", f"google:{sid}")
    acct = (p.get("externalAccountIdentifiers") or {}).get("obfuscatedExternalAccountId")
    owner = (existing or {}).get("user_id") or (_user_by_account_token(acct) or {}).get("id")
    sub = upsert("google", sid, owner, purchase_token=token, **_google_fields(p))
    return {"subscription_id": sub["id"], "status": sub["status"]}


# ------------------------------------------------------------- web (66, 69)

def web_notification(raw: bytes, signature: str) -> dict:
    """Provider-neutral contract until the web provider is chosen:
    HMAC-SHA256(raw body, ARCH_WEB_WEBHOOK_SECRET) in X-Signature, body
    {event_id, app_account_token, plan, status, period_end, trial_end,
    card_brand, card_last4}."""
    if not config.WEB_WEBHOOK_SECRET:
        raise ApiError("BILLING_NOT_CONFIGURED", "Web billing is not set up yet.", 503, {"route_to": None})
    want = hmac.new(config.WEB_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want, signature or ""):
        raise ApiError("WEBHOOK_UNAUTHORISED", "Unauthorised.", 401, {"route_to": None})
    ev = json.loads(raw)
    if not record_event("web", ev["event_id"], None, ev):
        return {"duplicate": True}
    owner = _user_by_account_token(ev.get("app_account_token"))
    if ev.get("status") not in ("trial", "active", "grace", "billing_retry", "cancelled", "expired") or \
            ev.get("plan") not in ("monthly", "annual"):
        raise ApiError("VALIDATION_ERROR", "Unknown status or plan.", 422)
    sub = upsert("web", ev.get("subscription_id") or ev["app_account_token"], owner["id"] if owner else None,
                 plan=ev["plan"], status=ev["status"], period_end=ev.get("period_end"),
                 trial_start=ev.get("trial_start"), trial_end=ev.get("trial_end"),
                 card_brand=ev.get("card_brand"), card_last4=ev.get("card_last4"),
                 will_renew=ev.get("will_renew", True))
    return {"subscription_id": sub["id"], "status": sub["status"]}


def dev_grant(user, plan="annual", status="trial", days=None) -> dict:
    """Dev / tests only: a membership without a store."""
    now = time.time()
    days = days if days is not None else config.TRIAL_DAYS
    return upsert("dev", user.id, user.id, plan=plan, status=status, period_end=now + days * DAY,
                  trial_start=now if status == "trial" else None,
                  trial_end=now + days * DAY if status == "trial" else None, will_renew=True,
                  grace_until=now + config.GRACE_DAYS * DAY if status == "grace" else None)


# ------------------------------------------------------------ screen data

def trial_dates(trial_start):
    """FREE UNTIL is the last free day, FIRST CHARGE the next day (trial from
    30 October -> 12 and 13 November)."""
    d0 = datetime.fromtimestamp(trial_start)
    free_until = d0 + timedelta(days=config.TRIAL_DAYS - 1)
    first = d0 + timedelta(days=config.TRIAL_DAYS)
    fmt = lambda d: f"{d.day} {d:%B %Y}"
    return fmt(free_until), fmt(first)


def price_line(plan):
    return f"{money(config.PRICE_ANNUAL)} per year" if plan == "annual" else f"{money(config.PRICE_MONTHLY)} per month"


def offer() -> dict:
    """Screen 64 (prices from config)."""
    save = config.PRICE_MONTHLY * 12 - config.PRICE_ANNUAL
    return {"title": "Unlock the full ARCH experience.", "line": "The part you do yourself.",
            "includes": ["Step-by-step tracing for every style", "Looks saved and kept", "New styles as they're added"],
            "trial": f"Start with {config.TRIAL_DAYS} days free.", "trial_days": config.TRIAL_DAYS,
            "plans": [{"id": "monthly", "label": "MONTHLY", "price": money(config.PRICE_MONTHLY),
                       "per": "PER MONTH", "amount": config.PRICE_MONTHLY, "currency": config.CURRENCY,
                       "name": config.PLAN_NAMES["monthly"], "best_value": False},
                      {"id": "annual", "label": "YEARLY", "price": money(config.PRICE_ANNUAL),
                       "per": "PER YEAR", "amount": config.PRICE_ANNUAL, "currency": config.CURRENCY,
                       "name": config.PLAN_NAMES["annual"], "best_value": True}],
            "saving": f"Save {money(save)} a year against paying monthly.",
            "cta": "BEGIN YOUR MEMBERSHIP", "footer": "Cancel at any point in Settings.",
            "products": {"apple": {v: k for k, v in config.APPLE_PRODUCTS.items()},
                         "google": {v: k for k, v in config.GOOGLE_PRODUCTS.items()}}}


def refund_line(platform):
    from app.catalogue.content import REFUND_WORDING
    return REFUND_WORDING.get({"apple": "ios", "google": "android"}.get(platform, platform))


def entitlements(user) -> dict:
    t = tier(user)
    out = {"tier": t, "is_member": t == "member", "renewal_date": None, "renewal_at": None,
           "can": {a: can(user, a) for a in ("scan", "tryon", "save_look", "trace", "guide")}}
    if user.is_guest:
        return out
    sub = current(user.id)
    out["app_account_token"] = app_account_token(user)
    out["offer"] = offer()
    if not sub:
        out["subscription"] = None
        return out
    plan_name = config.PLAN_NAMES.get(sub.get("plan"))
    out["subscription"] = {k: sub.get(k) for k in ("platform", "plan", "status", "period_end", "trial_start",
                                                    "trial_end", "grace_until", "will_renew", "product_id")}
    out["subscription"]["plan_name"] = plan_name
    out["subscription"]["access_until"] = _date(sub.get("period_end"))
    # The next charge: the end of the current period (or trial) while it is
    # set to renew. Cancelled / expired / not renewing: null.
    renews = sub.get("will_renew", True) and sub.get("status") in ("trial", "active", "grace", "billing_retry")
    out["renewal_at"] = sub.get("period_end") if renews else None
    out["renewal_date"] = _date(sub.get("period_end")) if renews else None
    out["subscription"]["renewal_date"] = out["renewal_date"]
    if sub.get("trial_start"):
        fu, fc = trial_dates(sub["trial_start"])
        out["screen_67"] = {"title": "Your free trial has begun.", "plan": plan_name, "free_until": fu,
                            "first_charge": fc, "then": price_line(sub.get("plan")),
                            "reminder": "We'll remind you 2 days before your trial ends.",
                            "cta": "ENTER ARCH", "cta_to": "20", "footer": "Manage your membership in Profile"}
    out["screen_63"] = {"current_plan": plan_name, "badge": "MEMBER" if t == "member" else None,
                        "unlocks": ["AR try-on sessions", "Style recommendations", "Tracing guide", "Saved looks"],
                        "cta": "MANAGE MEMBERSHIP", "cta_to": "70"}
    if t == "member":
        out["screen_71"] = {"title": "Cancel your membership.", "plan": plan_name,
                            "points": [f"Everything you have now stays with you until {_date(sub.get('period_end'))}.",
                                       refund_line(sub["platform"]),
                                       "Nothing more will be charged.",
                                       "Your looks, guides and profile stay with you."],
                            "how_to_cancel": "native" if sub["platform"] in ("apple", "google") else "web",
                            "cta": "CONFIRM CANCELLATION", "alt": "Keep my membership", "alt_to": "63"}
        out["screen_71"]["points"] = [p for p in out["screen_71"]["points"] if p]
    if sub["status"] == "grace":
        days = max(0, int(((sub.get("grace_until") or time.time()) - time.time()) // DAY))
        out["screen_68"] = {"title": "Something went wrong with your payment.",
                            "line": f"Your access continues for {days} days while we sort this.",
                            "grace_days_configured": config.GRACE_DAYS,
                            "cta": "UPDATE PAYMENT", "cta_to": "69" if sub["platform"] == "web" else "native",
                            "alt": "Remind me later"}
    if sub["status"] in ("cancelled", "expired"):
        last = db.list_for_user("looks", user.id, limit=1)
        out["screen_72"] = {"title": "Membership cancelled.",
                            "last_look": ({"caption": last[0].get("caption"),
                                           "image": (last[0].get("images") or {}).get("eyes")}
                                          if last else None),
                            "plan": plan_name, "access_until": _date(sub.get("period_end")),
                            "further_charges": "None", "confirmation": "Sent to email",
                            "line": "Your look will be here when you return.", "cta": "RETURN TO PROFILE",
                            "cta_to": "53"}
    if sub["platform"] == "web" and sub.get("card_last4"):
        out["payment_method"] = f"{sub.get('card_brand') or 'Card'} ···· {sub['card_last4']}"
    elif sub["platform"] in ("apple", "google"):
        out["payment_method"] = {"apple": "App Store", "google": "Google Play"}[sub["platform"]]
    return out


# ------------------------------------------------------------ scheduled jobs

def run_billing_jobs(now=None) -> dict:
    """Hourly: end lapsed access, send trial-ending (2 days before, even if
    notifications are off) and renewal reminders."""
    now = now or time.time()
    changed, sent = 0, 0
    for row in db.conn().execute("SELECT id FROM subscriptions").fetchall():
        sub = db.get("subscriptions", row["id"])
        st = sub["status"]
        if st in ("cancelled", "trial", "active") and sub.get("period_end") and sub["period_end"] <= now \
                and sub["platform"] in ("web", "dev"):
            upsert(sub["platform"], sub["original_transaction_id"], None, status="expired")
            changed += 1
            continue
        if st == "grace" and sub.get("grace_until") and sub["grace_until"] <= now:
            upsert(sub["platform"], sub["original_transaction_id"], None, status="billing_retry")
            changed += 1
            continue
        user = db.get("users", sub.get("user_id") or "")
        if not user or not user.get("email"):
            continue
        reminders = []
        if st == "trial" and sub.get("trial_end"):
            reminders.append(("trial_ending", sub["trial_end"] - 2 * DAY))
        if st == "active" and sub.get("will_renew") and sub.get("period_end"):
            if sub.get("plan") == "annual":
                reminders.append(("annual_renewal", sub["period_end"] - 30 * DAY))
            else:
                reminders.append(("monthly_anniversary", sub["period_end"] - 3 * DAY))
        for name, at in reminders:
            key = f"{name}:{int(sub.get('period_end') or 0)}"
            if at <= now < (sub.get("period_end") or now + 1) and key not in sub.get("reminders_sent", []):
                notify.send_email(user["email"], name, user_id=user["id"],
                                  plan=config.PLAN_NAMES.get(sub.get("plan")), date=_date(sub.get("period_end")))
                if name == "trial_ending":
                    notify.send_push(user["id"], name)
                sub.setdefault("reminders_sent", []).append(key)
                db.put("subscriptions", sub["id"], sub["user_id"], sub)
                sent += 1
    return {"status_changes": changed, "reminders_sent": sent}
