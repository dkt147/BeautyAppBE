from fastapi import APIRouter, Depends

from bson import ObjectId

from app.database import db
from app.auth.utils import get_current_user
from app.auth.schemas import UserResponse
from app.onboarding.schemas import OnboardingRequest

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/complete", response_model=UserResponse)
async def complete_onboarding(data: OnboardingRequest, user=Depends(get_current_user)):
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {
            "onboarding.has_used_before": data.has_used_before,
            "onboarding.permissions_granted": data.permissions_granted,
            "onboarding.completed": True,
        }},
    )
    updated = await db.users.find_one({"_id": ObjectId(user["id"])})
    return UserResponse(
        id=str(updated["_id"]),
        email=updated["email"],
        full_name=updated["full_name"],
        onboarding=updated.get("onboarding", {}),
        profile_image=updated.get("profile_image"),
        catalog_image=updated.get("catalog_image"),
    )
