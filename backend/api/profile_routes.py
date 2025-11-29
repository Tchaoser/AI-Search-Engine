from typing import Optional
from fastapi import APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from services.user_profile_service import build_user_profile
from services.db import user_profiles_col
from api.utils import get_user_id_from_auth

router = APIRouter()


# --- Request models ---

class UserOverride(BaseModel):
    """Optional body model to allow admin override of user_id."""
    user_id: Optional[str] = None


# --- Helper functions ---

def get_effective_user(auth_user, user_id):
    """Return the effective user, prioritizing auth_user unless guest."""
    return auth_user if auth_user and auth_user != "guest" else (user_id or "guest")


def remove_from_implicit(profile, keyword):
    """Remove keyword from implicit_exclusions and implicit_interests."""
    # Remove from exclusions
    exclusions = profile.get("implicit_exclusions", [])
    profile["implicit_exclusions"] = [e for e in exclusions if e.lower() != keyword.lower()]

    # Remove from implicit interests
    if "implicit_interests" in profile and profile.get("implicit_interests"):
        profile["implicit_interests"] = {
            k: v for k, v in profile["implicit_interests"].items() if k.lower() != keyword.lower()
        }


def promote_to_explicit(profile, keyword, weight=1.0):
    """Add a keyword as explicit interest and remove it from implicit lists."""
    # Check for duplicate
    existing_keywords = {e["keyword"].lower() for e in profile.get("explicit_interests", [])}
    if keyword.lower() in existing_keywords:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # Append new explicit interest
    profile.setdefault("explicit_interests", []).append({
        "keyword": keyword,
        "weight": weight,
        "last_updated": datetime.utcnow().isoformat()
    })

    # Remove from implicit exclusions and implicit interests
    remove_from_implicit(profile, keyword)


# --- Endpoints ---

@router.get("/profiles/me")
async def get_my_profile(user_id: str = Depends(get_user_id_from_auth)):
    profile = build_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile


@router.get("/profiles/{user_id}")
async def get_user_profile(user_id: str):
    profile = build_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile


@router.post("/profiles/explicit/add")
async def add_explicit_interest(
        user_id: str = Body(None),
        keyword: str = Body(...),
        weight: float = Body(1.0),
        auth_user: str = Depends(get_user_id_from_auth)
):
    effective_user = get_effective_user(auth_user, user_id)
    profile = build_user_profile(effective_user)
    promote_to_explicit(profile, keyword, weight)

    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": profile},
        upsert=True
    )
    return profile


@router.put("/profiles/explicit/bulk_update")
async def bulk_update_explicit_interests(
        user_id: str = Body(None),
        updates: list = Body(...),
        auth_user: str = Depends(get_user_id_from_auth)
):
    effective_user = get_effective_user(auth_user, user_id)
    profile = build_user_profile(effective_user)

    # Map current explicit interests for quick update
    keyword_map = {e["keyword"].lower(): e for e in profile.get("explicit_interests", [])}

    for item in updates:
        kw = item["keyword"]
        wt = float(item.get("weight", 1.0))
        key = kw.lower()

        if key in keyword_map:
            # Update weight and timestamp
            keyword_map[key]["weight"] = wt
            keyword_map[key]["last_updated"] = datetime.utcnow().isoformat()
        else:
            # Add new explicit interest
            promote_to_explicit(profile, kw, wt)

    # Replace explicit interests list with updated map values
    profile["explicit_interests"] = list(keyword_map.values()) + [
        e for e in profile.get("explicit_interests", [])
        if e["keyword"].lower() not in keyword_map
    ]

    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": profile},
        upsert=True
    )
    return profile


@router.delete("/profiles/explicit/remove")
async def remove_explicit_interest(
        user_id: str = Body(None),
        keyword: str = Body(...),
        auth_user: str = Depends(get_user_id_from_auth)
):
    effective_user = get_effective_user(auth_user, user_id)
    profile = build_user_profile(effective_user)

    profile["explicit_interests"] = [
        e for e in profile.get("explicit_interests", [])
        if e["keyword"].lower() != keyword.lower()
    ]

    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": profile},
        upsert=True
    )
    return profile


@router.delete("/profiles/implicit/remove")
async def remove_implicit_interest(
        user_id: str = Body(None),
        keyword: str = Body(...),
        auth_user: str = Depends(get_user_id_from_auth)
):
    effective_user = get_effective_user(auth_user, user_id)

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword required")

    existing_profile = user_profiles_col.find_one({"user_id": effective_user}) or {}
    exclusions = existing_profile.get("implicit_exclusions", [])

    if keyword.lower() not in (e.lower() for e in exclusions):
        exclusions.append(keyword)
        user_profiles_col.update_one(
            {"user_id": effective_user},
            {"$set": {"implicit_exclusions": exclusions}},
            upsert=True
        )

    profile = build_user_profile(effective_user)
    return profile


@router.delete("/profiles/implicit/exclusion/remove")
async def remove_implicit_exclusion(
        user_id: str = Body(None),
        keyword: str = Body(...),
        auth_user: str = Depends(get_user_id_from_auth)
):
    """Undo a previously excluded implicit interest"""
    effective_user = get_effective_user(auth_user, user_id)

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword required")

    existing_profile = user_profiles_col.find_one({"user_id": effective_user}) or {}
    exclusions = existing_profile.get("implicit_exclusions", [])

    # Remove the keyword from exclusions
    exclusions = [e for e in exclusions if e.lower() != keyword.lower()]
    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": {"implicit_exclusions": exclusions}},
        upsert=True
    )

    profile = build_user_profile(effective_user)
    return profile


# --- Clear endpoints (clean FastAPI-friendly model for optional override) ---

@router.post("/profiles/explicit/clear")
async def clear_all_explicit_interests(
        payload: UserOverride = Body(None),
        auth_user: str = Depends(get_user_id_from_auth)
):
    """
    Remove all explicit interests for the effective user.
    This is destructive (deletes explicit interests).
    """
    effective_user = get_effective_user(auth_user, payload.user_id if payload else None)

    profile = build_user_profile(effective_user)
    profile["explicit_interests"] = []

    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": profile},
        upsert=True
    )
    return profile


@router.post("/profiles/implicit/clear")
async def clear_all_implicit_interests(
        payload: UserOverride = Body(None),
        auth_user: str = Depends(get_user_id_from_auth)
):
    """
    Move all implicit interest keywords into implicit_exclusions (undoable).
    This prevents them from showing up as implicit interests.

    Accepts optional JSON body: {"user_id": "<id>"} to act on a different user (admin override).
    """
    effective_user = get_effective_user(auth_user, payload.user_id if payload else None)

    # Use the rebuilt profile to get the current implicit_interests keys
    profile = build_user_profile(effective_user)
    implicit_keys = list(profile.get("implicit_interests", {}).keys())

    # Read stored profile to update exclusions (preserve case & existing exclusions)
    stored = user_profiles_col.find_one({"user_id": effective_user}) or {}
    current_exclusions = stored.get("implicit_exclusions", []) or []

    # Add implicit keys to exclusions (case-insensitive dedupe)
    lower_excl = {e.lower() for e in current_exclusions}
    for k in implicit_keys:
        if k.lower() not in lower_excl:
            current_exclusions.append(k)
            lower_excl.add(k.lower())

    # Persist updated exclusions
    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": {"implicit_exclusions": current_exclusions}},
        upsert=True
    )

    # Rebuild profile so implicit_interests are recalculated without these keys
    profile = build_user_profile(effective_user)
    return profile
