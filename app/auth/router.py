from fastapi import APIRouter, HTTPException, status, Depends

from bson import ObjectId

from app.database import db
from app.auth.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    UpdateProfileRequest, ChangeEmailRequest, ChangePasswordRequest, MessageResponse,
)
from app.auth.service import create_user, authenticate_user
from app.auth.utils import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    user = await create_user(data)
    if user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    token = create_access_token(str(user["_id"]))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    user = await authenticate_user(data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user["_id"]))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        onboarding=user.get("onboarding", {}),
        profile_image=user.get("profile_image"),
        catalog_image=user.get("catalog_image"),
    )


def _user_response(u: dict) -> UserResponse:
    return UserResponse(
        id=str(u["_id"]),
        email=u["email"],
        full_name=u["full_name"],
        onboarding=u.get("onboarding", {}),
        profile_image=u.get("profile_image"),
        catalog_image=u.get("catalog_image"),
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(data: UpdateProfileRequest, user=Depends(get_current_user)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": updates})
    updated = await db.users.find_one({"_id": ObjectId(user["id"])})
    return _user_response(updated)


@router.put("/change-email", response_model=UserResponse)
async def change_email(data: ChangeEmailRequest, user=Depends(get_current_user)):
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password")
    existing = await db.users.find_one({"email": data.new_email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")
    await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"email": data.new_email}})
    updated = await db.users.find_one({"_id": ObjectId(user["id"])})
    return _user_response(updated)


@router.put("/change-password", response_model=MessageResponse)
async def change_password(data: ChangePasswordRequest, user=Depends(get_current_user)):
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect current password")
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"password_hash": hash_password(data.new_password)}},
    )
    return MessageResponse(message="Password changed successfully")


@router.delete("/account", response_model=MessageResponse)
async def delete_account(user=Depends(get_current_user)):
    await db.users.delete_one({"_id": ObjectId(user["id"])})
    return MessageResponse(message="Account deleted successfully")
