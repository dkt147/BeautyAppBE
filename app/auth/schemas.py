from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OnboardingStatus(BaseModel):
    has_used_before: bool = False
    permissions_granted: bool = False
    completed: bool = False


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    onboarding: OnboardingStatus = OnboardingStatus()
    profile_image: Optional[str] = None
    catalog_image: Optional[str] = None
