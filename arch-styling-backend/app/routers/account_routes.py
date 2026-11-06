"""Block 3 routes: recommendations 41-43 (M6), preferences 56-57 (M3),
looks rename / share 50, 52 (M8), devices 82 (M11), membership and billing
13, 63-72 (M10), support 59 (M13)."""
import hashlib
import time
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, EmailStr, Field

from app import config
from app.catalogue import content as C
from app.core import db
from app.core.auth import User, current_user, require
from app.core.devtools import IS_DEV, dev_only
from app.core.errors import ApiError
from app.core.ratelimit import limit
from app.services import billing_service as B
from app.services import looks_service as LS
from app.services import notify
from app.services import recommend_service as R
from app.services.profile_service import get_preferences, update_preferences

router = APIRouter()


def _account(user: User, gate="13a") -> User:
    require(user, "account", gate=gate)
    return user


# ============================================================ M6 (41-43)

@router.get("/v1/recommendations", tags=["Recommendation 41-43"],
            summary="41 Your Result: face shape, the two recommended styles (Table 2), avoid, her own pick")
def recommendations(user: User = Depends(current_user)):
    require(user, "recommend", gate="13")
    return R.recommendations(user)


@router.get("/v1/recommendations/{style}", tags=["Recommendation 41-43"],
            summary="42 Why This Shape (about the style) and 43 (why it suits her face, outline on her photo)")
def recommendation_detail(style: str, user: User = Depends(current_user)):
    require(user, "recommend", gate="13")
    return R.why(user, style)


# ============================================================ M3 (56, 57)

class PreferencesIn(BaseModel):
    notifications_on: Optional[bool] = Field(None, description="56 Notifications")
    auto_save_looks: Optional[bool] = Field(None, description="56 Auto-save looks")
    camera_auto_detect: Optional[bool] = Field(None, description="56 Camera auto-detect")
    language: Optional[str] = Field(None, description="57: en-GB, fr, es, de, ja, zh")


@router.get("/v1/me/preferences", tags=["Preferences 56-57"], summary="56 Preferences and 57 the six languages")
def preferences(user: User = Depends(current_user)):
    return {"preferences": get_preferences(_account(user).id), "languages": C.LANGUAGES}


@router.patch("/v1/me/preferences", tags=["Preferences 56-57"],
              summary="56 SAVE CHANGES / 57 SAVE PREFERENCE -> 53")
def patch_preferences(body: PreferencesIn, user: User = Depends(current_user)):
    _account(user)
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise ApiError("VALIDATION_ERROR", "Nothing to change.", 422)
    if "language" in fields and fields["language"] not in C.LANGUAGE_IDS:
        raise ApiError("VALIDATION_ERROR", f"Unknown language. Use one of: {', '.join(C.LANGUAGE_IDS)}.", 422)
    return {"preferences": update_preferences(user.id, **fields), "next_screen": "53"}


# ============================================================ M8 (50, 52)

def _own_look(user, look_id):
    lk = db.get("looks", look_id)
    if not lk or lk["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Look not found.", 404)
    return lk


class LookPatchIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=60, description="The look's new name")


@router.patch("/v1/looks/{look_id}", tags=["Looks 37-38"], summary="50 rename a look")
def patch_look(look_id: str, body: LookPatchIn, user: User = Depends(current_user)):
    _account(user)
    return {"look": LS.rename(_own_look(user, look_id), body.name)}


@router.post("/v1/looks/{look_id}/share-image", tags=["Looks 37-38"],
             summary="52 Share This Look: one image with the look's name (Save as image / Share via message)")
def share_image(look_id: str, user: User = Depends(current_user)):
    _account(user)
    return LS.share_image(_own_look(user, look_id))


# ============================================================ M11 (82)

class DeviceIn(BaseModel):
    platform: Literal["ios", "android"]
    push_token: str = Field(..., min_length=8, max_length=4096)
    permission: Literal["granted", "denied", "not_determined"] = Field(
        "granted", description="83: the answer to the native dialog")
    app_version: Optional[str] = Field(None, max_length=40)


@router.post("/v1/devices", status_code=201, tags=["Notifications 82-83"],
             summary="82 YES, KEEP ME INFORMED -> 83 -> register this device's push token")
def register_device(body: DeviceIn, user: User = Depends(current_user)):
    _account(user)
    did = "dev_" + hashlib.sha256(body.push_token.encode()).hexdigest()[:24]
    old = db.get("devices", did)
    if old and old["user_id"] != user.id:            # the phone changed hands: move it
        db.delete("devices", did)
    doc = {"id": did, "user_id": user.id, "platform": body.platform, "push_token": body.push_token,
           "permission": body.permission, "app_version": body.app_version, "updated_at": time.time()}
    db.put("devices", did, user.id, doc)
    flags = user.doc.setdefault("flags", {})
    if not flags.get("notification_prompt_seen"):
        flags["notification_prompt_seen"] = True
        db.put("users", user.id, user.id, user.doc)
    return {"device": {k: v for k, v in doc.items() if k != "push_token"}}


@router.get("/v1/devices", tags=["Notifications 82-83"], summary="Her registered devices")
def list_devices(user: User = Depends(current_user)):
    _account(user)
    return {"devices": [{k: v for k, v in d.items() if k != "push_token"}
                        for d in db.list_for_user("devices", user.id, limit=50)],
            "notification_prompt_seen": user.doc.get("flags", {}).get("notification_prompt_seen", False)}


@router.delete("/v1/devices/{device_id}", tags=["Notifications 82-83"], summary="Stop push to this device")
def delete_device(device_id: str, user: User = Depends(current_user)):
    _account(user)
    d = db.get("devices", device_id)
    if not d or d["user_id"] != user.id:
        raise ApiError("NOT_FOUND", "Device not found.", 404)
    db.delete("devices", device_id)
    return {"deleted": device_id}


# ============================================================ M10 (13, 63-72)

TAG_B = "Membership 13, 63-72"


@router.get("/v1/me/entitlements", tags=[TAG_B],
            summary="Tier (guest / free / member), what she can do, and the data for 63, 64, 67, 68, 71, 72")
def entitlements(user: User = Depends(current_user)):
    return B.entitlements(user)


class AppleVerifyIn(BaseModel):
    signed_transaction: str = Field(..., description="JWS from StoreKit 2 (Transaction.jwsRepresentation)")


@router.post("/v1/billing/apple/verify", tags=[TAG_B], summary="After the native purchase sheet: confirm on the server -> 65")
def apple_verify(body: AppleVerifyIn, user: User = Depends(current_user)):
    sub = B.apple_verify(_account(user, "13"), body.signed_transaction)
    return {**B.entitlements(user), "next_screen": "65", "subscription_status": sub["status"]}


class GoogleVerifyIn(BaseModel):
    purchase_token: str


@router.post("/v1/billing/google/verify", tags=[TAG_B], summary="After the Play purchase: confirm on the server -> 65")
def google_verify(body: GoogleVerifyIn, user: User = Depends(current_user)):
    sub = B.google_verify(_account(user, "13"), body.purchase_token)
    return {**B.entitlements(user), "next_screen": "65", "subscription_status": sub["status"]}


class RestoreIn(BaseModel):
    platform: Literal["apple", "google"]
    signed_transactions: List[str] = Field(default_factory=list, description="Apple: current entitlements as JWS")
    purchase_tokens: List[str] = Field(default_factory=list, description="Google: active purchase tokens")


@router.post("/v1/billing/restore", tags=[TAG_B], summary="66 Restore purchase (native restore, confirmed here)")
def restore(body: RestoreIn, user: User = Depends(current_user)):
    _account(user, "13")
    items = body.signed_transactions if body.platform == "apple" else body.purchase_tokens
    if not items:
        raise ApiError("VALIDATION_ERROR", "Nothing to restore.", 422)
    for it in items[:20]:
        (B.apple_verify if body.platform == "apple" else B.google_verify)(user, it)
    return B.entitlements(user)


@router.post("/v1/billing/web/checkout", tags=[TAG_B], summary="66 / 69 web payment (provider not chosen yet)")
def web_checkout(user: User = Depends(current_user)):
    _account(user, "13")
    raise ApiError("BILLING_NOT_CONFIGURED", "Web payments are not set up yet.", 503, {"route_to": None})


@router.post("/v1/webhooks/apple", tags=["Store webhooks"], summary="App Store Server Notifications v2")
def apple_webhook(body: dict):
    if not body.get("signedPayload"):
        raise ApiError("VALIDATION_ERROR", "signedPayload is required.", 422)
    return B.apple_notification(body["signedPayload"])


@router.post("/v1/webhooks/google", tags=["Store webhooks"], summary="Google Play RTDN (Pub/Sub push)")
def google_webhook(body: dict, authorization: Optional[str] = Header(None)):
    scheme, _, tok = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not tok:
        raise ApiError("WEBHOOK_UNAUTHORISED", "Unauthorised.", 401, {"route_to": None})
    B.verify_pubsub_token(tok)
    return B.google_notification(body)


@router.post("/v1/webhooks/web", tags=["Store webhooks"], summary="Web billing provider (HMAC-signed)")
async def web_webhook(request: Request, x_signature: Optional[str] = Header(None)):
    return B.web_notification(await request.body(), x_signature)


class DevGrantIn(BaseModel):
    plan: Literal["monthly", "annual"] = "annual"
    status: Literal["trial", "active", "grace", "billing_retry", "cancelled", "expired"] = "trial"
    days: Optional[int] = None


@router.post("/v1/dev/grant-membership", tags=["Dev tools"], dependencies=[Depends(dev_only)],
             include_in_schema=IS_DEV, summary="Dev only: membership without a store")
def dev_grant(body: DevGrantIn, user: User = Depends(current_user)):
    B.dev_grant(_account(user), body.plan, body.status, body.days)
    return B.entitlements(user)


# ============================================================ M13 (59)

class SupportIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    message: str = Field(..., min_length=2, max_length=4000)


@router.post("/v1/support/messages", status_code=201, tags=["Support 58-61"],
             dependencies=[Depends(limit("support", 5, 3600))],
             summary="59 SEND MESSAGE (to office@cbygroyals.com) -> confirmation, then 53 (route to confirm)")
def support_message(body: SupportIn, user: User = Depends(current_user)):
    mid = db.new_id("sup")
    uid = None if user.is_guest else user.id
    doc = {"id": mid, "account_id": uid, "name": body.name.strip(), "email": body.email, "body": body.message.strip(),
           "sent_at": time.time()}
    db.put("support_messages", mid, uid, doc)
    notify.send_email(config.SUPPORT_EMAIL, "support_message", user_id=uid, message_id=mid,
                      name=doc["name"], reply_to=body.email, body=doc["body"])
    return {"message_id": mid, "sent": True, "title": "Thank you.",
            "line": f"We read every message. We'll reply to {body.email}.",
            "next_screen": "53", "route_to_confirm": True}
