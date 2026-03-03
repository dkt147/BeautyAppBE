from fastapi import APIRouter, HTTPException, status, Depends

from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.auth.service import create_user, authenticate_user
from app.auth.utils import create_access_token, get_current_user

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
