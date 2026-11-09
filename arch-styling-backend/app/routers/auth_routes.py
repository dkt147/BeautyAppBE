"""Screens 04 to 11, 53, 54, 65, 81 and the kept Change Password step:
accounts and sessions (module M1)."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, EmailStr, Field

from app.core.auth import User, current_user, require, user_from_token
from app.core.errors import ApiError
from app.core.ratelimit import guarded_login, guarded_register, limit
from app.services import auth_service as A
from app.services import billing_service as B
from app.services import consent_service as CS
from app.services.profile_service import get_profile

router = APIRouter()
TAG = "Accounts 04-11, 53-54, 65, 81"


def _device(user_agent: Optional[str]):
    return (user_agent or "")[:200] or None


def _linked(result: dict, install_id: Optional[str]) -> dict:
    """Attach screen 02 consent records made on this install (M2)."""
    if install_id and result.get("user"):
        CS.link_install(install_id.strip()[:100], result["user"]["id"])
    return result


INSTALL = Header(None, description="App install id; links the screen 02 consent to this account")


def _account(user: User) -> User:
    require(user, "account", gate="13a")
    return user


# ---------------------------------------------------------------- sign up / in

class RegisterIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="YOUR NAME on 05")
    email: EmailStr
    password: str = Field(..., max_length=200)
    confirm_password: Optional[str] = Field(None, description="CONFIRM PASSWORD on 05. Mismatch -> 06.")


@router.post("/v1/auth/register", status_code=201, tags=[TAG],
             summary="05 CREATE ACCOUNT -> 14 (409 EMAIL_REGISTERED -> 07, field errors -> 06)")
def register(body: RegisterIn, request: Request, user_agent: Optional[str] = Header(None),
             x_install_id: Optional[str] = INSTALL):
    # Rate limit: successful sign-ups per address, failures per email (ratelimit.py).
    result = guarded_register(request, body.email, lambda: A.register(
        body.name, body.email, body.password, body.confirm_password, _device(user_agent)))
    return _linked(result, x_install_id)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=200)


@router.post("/v1/auth/login", tags=[TAG],
             summary="08 SIGN IN -> 11 (two-factor) or 14 / 20 / 21")
def login(body: LoginIn, request: Request, user_agent: Optional[str] = Header(None),
          x_install_id: Optional[str] = INSTALL):
    # Rate limit: failed attempts only, per email and per address (ratelimit.py).
    result = guarded_login(request, body.email, lambda: A.login(body.email, body.password, _device(user_agent)))
    return _linked(result, x_install_id)


class SocialIn(BaseModel):
    id_token: str = Field(..., description="Identity token from Sign in with Apple / Google Sign-In")
    name: Optional[str] = Field(None, description="Apple sends the name only on the first sign-in")


@router.post("/v1/auth/apple", tags=[TAG], dependencies=[Depends(limit("social", 20, 300))], summary="05 / 08 Continue with Apple")
def apple(body: SocialIn, user_agent: Optional[str] = Header(None), x_install_id: Optional[str] = INSTALL):
    return _linked(A.social_sign_in("apple", body.id_token, body.name, _device(user_agent)), x_install_id)


@router.post("/v1/auth/google", tags=[TAG], dependencies=[Depends(limit("social", 20, 300))], summary="05 / 08 Continue with Google")
def google(body: SocialIn, user_agent: Optional[str] = Header(None), x_install_id: Optional[str] = INSTALL):
    return _linked(A.social_sign_in("google", body.id_token, body.name, _device(user_agent)), x_install_id)


# -------------------------------------------------------------------- 2FA (11)

class TwoFactorIn(BaseModel):
    pending_token: str = Field(..., description="From the sign-in response when two_factor_required is true")
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class PendingIn(BaseModel):
    pending_token: str


@router.post("/v1/auth/2fa/verify", tags=[TAG], dependencies=[Depends(limit("2fa", 10, 300))], summary="11 VERIFY CODE -> 14 / 20 / 21")
def two_factor_verify(body: TwoFactorIn, user_agent: Optional[str] = Header(None),
                      x_install_id: Optional[str] = INSTALL):
    user = user_from_token(body.pending_token, allowed_types=("2fa_pending",))
    return _linked(A.verify_two_factor(user, body.code, _device(user_agent)), x_install_id)


@router.post("/v1/auth/2fa/resend", tags=[TAG], summary="11 Resend code (429 RESEND_TOO_SOON with retry_after)")
def two_factor_resend(body: PendingIn):
    user = user_from_token(body.pending_token, allowed_types=("2fa_pending",))
    return A.resend_two_factor(user)


# ------------------------------------------------------------------ passwords

class ForgotIn(BaseModel):
    email: EmailStr


@router.post("/v1/auth/password/forgot", tags=[TAG], dependencies=[Depends(limit("forgot", 5, 900))], summary="09 SEND RESET LINK -> 10 (also 10 Send again)")
def forgot(body: ForgotIn):
    return A.forgot_password(body.email)


class ResetIn(BaseModel):
    token: str = Field(..., description="The token from the reset link")
    new_password: str = Field(..., max_length=200)
    confirm_password: Optional[str] = None


@router.post("/v1/auth/password/reset", tags=[TAG], summary="Set new password (kept step) -> 08")
def reset(body: ResetIn):
    return A.reset_password(body.token, body.new_password, body.confirm_password)


class ChangePasswordIn(BaseModel):
    current_password: Optional[str] = Field(None, description="Not needed for an Apple / Google-only account")
    new_password: str = Field(..., max_length=200)
    confirm_password: Optional[str] = None


@router.post("/v1/me/password", tags=[TAG], summary="Change Password (kept step). Signs out other devices.")
def change_password(body: ChangePasswordIn, user: User = Depends(current_user)):
    return A.change_password(_account(user), body.current_password, body.new_password, body.confirm_password)


# ------------------------------------------------------------------- sessions

class RefreshIn(BaseModel):
    refresh_token: str


@router.post("/v1/auth/refresh", tags=[TAG], summary="New access token; the refresh token rotates")
def refresh(body: RefreshIn):
    return A.refresh_session(body.refresh_token)


@router.post("/v1/auth/logout", tags=[TAG], summary="81 SIGN OUT -> 08: ends this session")
def logout(user: User = Depends(current_user)):
    if not user.is_guest and user.session_id:
        A.revoke_session(user.session_id)
    return {"signed_out": True, "next_screen": "08"}


# ------------------------------------------------------------------ me (53, 54)

@router.get("/v1/me", tags=[TAG], summary="53 / 54 Her account, flags and brow profile")
def me(user: User = Depends(current_user)):
    if user.is_guest:
        return {"user": {"id": None, "name": "Guest", "is_guest": True}, "flags": {}, "profile": None}
    ent = B.entitlements(user)
    sub = ent.get("subscription") or {}
    return {"user": A.public_user(user.doc), "flags": user.doc.get("flags", {}), "profile": get_profile(user.id),
            "membership": {"tier": ent["tier"], "badge": "MEMBER" if ent["is_member"] else None,
                           "plan": sub.get("plan_name"), "status": sub.get("status"),
                           "renews": sub.get("access_until") if sub.get("will_renew") else None,
                           "access_until": sub.get("access_until"),
                           "payment_method": ent.get("payment_method")}}


class MeIn(BaseModel):
    name: Optional[str] = Field(None, max_length=80, description="FULL NAME on 54")
    email: Optional[EmailStr] = Field(None, description="EMAIL ADDRESS on 54 (needs current_password)")
    current_password: Optional[str] = None
    two_factor: Optional[bool] = Field(None, description="Ask for a code at sign-in (screen 11)")


@router.patch("/v1/me", tags=[TAG], summary="54 SAVE CHANGES")
def patch_me(body: MeIn, user: User = Depends(current_user)):
    _account(user)
    if body.name is None and body.email is None and body.two_factor is None:
        raise ApiError("VALIDATION_ERROR", "Nothing to change.", 422)
    return {"user": A.update_me(user, body.name, body.email, body.current_password, body.two_factor)}


class PhoneIn(BaseModel):
    dial_code: str = Field(..., examples=["+1"], description="COUNTRY on 65, e.g. +1")
    number: str = Field(..., examples=["5551234567"])


class CodeIn(BaseModel):
    code: str = Field(..., pattern=r"^\d{6}$")


@router.post("/v1/me/phone", tags=[TAG], summary="65 CONTINUE: text a code to this number (Not now -> 67, no call)")
def phone(body: PhoneIn, user: User = Depends(current_user)):
    return A.start_phone(_account(user), body.dial_code, body.number)


@router.post("/v1/me/phone/verify", tags=[TAG], summary="65 confirm the code -> 67")
def phone_verify(body: CodeIn, user: User = Depends(current_user)):
    return A.verify_phone(_account(user), body.code)
