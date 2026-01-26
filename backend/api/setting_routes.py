from fastapi import APIRouter, Depends, Body
from services.db import user_profiles_col
from api.utils import get_user_id_from_auth

router = APIRouter()

# Defaults
DEFAULT_SETTINGS = {
    "use_enhanced_query": True,
    "verbosity": "medium",
    "semantic_mode": "clarify_only",
}

# User resolution

def get_effective_user(auth_user: str, user_id: str | None):
    """
    Match profile behavior exactly:
    - authenticated user wins (unless guest)
    - fallback to provided user_id
    - final fallback: guest
    """
    if auth_user and auth_user != "guest":
        return auth_user
    if user_id:
        return user_id
    return "guest"

# GET settings
@router.get("/user/settings")
async def get_settings(
    user_id: str | None = None,
    auth_user: str = Depends(get_user_id_from_auth),
):
    effective_user = get_effective_user(auth_user, user_id)

    doc = user_profiles_col.find_one({"user_id": effective_user})

    if not doc:
        user_profiles_col.insert_one({
            "user_id": effective_user,
            "settings": DEFAULT_SETTINGS.copy()
        })
        return DEFAULT_SETTINGS

    existing = doc.get("settings", {})
    merged = {**DEFAULT_SETTINGS, **existing}

    if existing != merged:
        user_profiles_col.update_one(
            {"user_id": effective_user},
            {"$set": {"settings": merged}}
        )

    return merged

# UPDATE settings
@router.post("/user/settings")
async def update_settings(
    update: dict = Body(...),
    user_id: str | None = None,
    auth_user: str = Depends(get_user_id_from_auth),
):
    effective_user = get_effective_user(auth_user, user_id)

    # Update ONLY settings fields
    user_profiles_col.update_one(
        {"user_id": effective_user},
        {
            "$set": {
                **{f"settings.{k}": v for k, v in update.items()},
                "user_id": effective_user,
            }
        },
        upsert=True,
    )

    doc = user_profiles_col.find_one({"user_id": effective_user})
    return doc.get("settings", DEFAULT_SETTINGS)
