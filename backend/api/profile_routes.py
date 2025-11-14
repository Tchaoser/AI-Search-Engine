from fastapi import APIRouter, Body, HTTPException, Depends
from datetime import datetime
from services.user_profile_service import build_user_profile
from services.db import user_profiles_col
from api.utils import get_user_id_from_auth

router = APIRouter()


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
    effective_user = (
        auth_user if auth_user and auth_user != "guest"
        else (user_id or "guest")
    )

    profile = build_user_profile(effective_user)

    for e in profile["explicit_interests"]:
        if e["keyword"].lower() == keyword.lower():
            raise HTTPException(status_code=400, detail="Keyword already exists")

    profile["explicit_interests"].append({
        "keyword": keyword,
        "weight": weight,
        "last_updated": datetime.utcnow().isoformat()
    })

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
    effective_user = (
        auth_user if auth_user and auth_user != "guest"
        else (user_id or "guest")
    )

    profile = build_user_profile(effective_user)
    keyword_map = {e["keyword"].lower(): e for e in profile["explicit_interests"]}

    for item in updates:
        kw = item["keyword"]
        wt = float(item.get("weight", 1.0))
        key = kw.lower()

        if key in keyword_map:
            keyword_map[key]["weight"] = wt
            keyword_map[key]["last_updated"] = datetime.utcnow().isoformat()
        else:
            profile["explicit_interests"].append({
                "keyword": kw,
                "weight": wt,
                "last_updated": datetime.utcnow().isoformat()
            })

    profile["explicit_interests"] = list(keyword_map.values())

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
    effective_user = (
        auth_user if auth_user and auth_user != "guest"
        else (user_id or "guest")
    )

    profile = build_user_profile(effective_user)
    profile["explicit_interests"] = [
        e for e in profile["explicit_interests"]
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
    effective_user = (
        auth_user if auth_user and auth_user != "guest"
        else (user_id or "guest")
    )

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
