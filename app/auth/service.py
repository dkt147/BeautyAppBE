from app.database import db
from app.auth.schemas import RegisterRequest
from app.auth.utils import hash_password, verify_password


async def create_user(data: RegisterRequest) -> dict:
    existing = await db.users.find_one({"email": data.email})
    if existing:
        return None

    user_doc = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "onboarding": {
            "has_used_before": False,
            "permissions_granted": False,
            "completed": False,
        },
        "profile_image": None,
        "catalog_image": None,
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc


async def authenticate_user(email: str, password: str) -> dict | None:
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user
