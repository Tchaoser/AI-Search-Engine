from fastapi import APIRouter, Body, HTTPException, Depends
from datetime import datetime
from services.user_profile_service import build_user_profile
from services.db import user_profiles_col
from services.logger import AppLogger
from api.utils import get_user_id_from_auth

router = APIRouter()
logger = AppLogger.get_logger(__name__)


@router.get("/profiles/me")
async def get_my_profile(user_id: str = Depends(get_user_id_from_auth)):
    logger.debug("Fetching profile", extra={"user_id": user_id})
    profile = build_user_profile(user_id)
    if not profile:
        logger.warning("Profile not found", extra={"user_id": user_id})
        raise HTTPException(status_code=404, detail="User profile not found")
    logger.debug("Profile fetched", extra={
        "user_id": user_id,
        "implicit_count": len(profile.get("implicit_interests", {})),
        "explicit_count": len(profile.get("explicit_interests", []))
    })
    return profile


@router.get("/profiles/{user_id}")
async def get_user_profile(user_id: str):
    logger.debug("Fetching profile for user", extra={"user_id": user_id})
    profile = build_user_profile(user_id)
    if not profile:
        logger.warning("Profile not found", extra={"user_id": user_id})
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
            logger.warning("Duplicate explicit interest", extra={
                "user_id": effective_user,
                "keyword": keyword
            })
            raise HTTPException(status_code=400, detail="Keyword already exists")

    profile["explicit_interests"].append({
        "keyword": keyword,
        "weight": weight,
        "last_updated": datetime.utcnow().isoformat()
    })

    # If the user had previously excluded this keyword from implicit interests,
    # remove it from implicit_exclusions so explicit interest takes precedence.
    exclusions = profile.get("implicit_exclusions", [])
    if any(e.lower() == keyword.lower() for e in exclusions):
        exclusions = [e for e in exclusions if e.lower() != keyword.lower()]
        profile["implicit_exclusions"] = exclusions

    # Also remove the newly explicit keyword from implicit_interests
    # so it won't be present on the returned profile.
    if "implicit_interests" in profile and profile.get("implicit_interests"):
        profile["implicit_interests"] = {
            k: v for k, v in profile["implicit_interests"].items()
            if k.lower() != keyword.lower()
        }

    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": profile},
        upsert=True
    )
    logger.info("Explicit interest added", extra={
        "user_id": effective_user,
        "keyword": keyword,
        "weight": weight
    })

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
            # If this new explicit interest was previously excluded as implicit,
            # remove it from the implicit_exclusions so explicit wins.
            exclusions = profile.get("implicit_exclusions", [])
            if any(e.lower() == kw.lower() for e in exclusions):
                exclusions = [e for e in exclusions if e.lower() != kw.lower()]
                profile["implicit_exclusions"] = exclusions
            # Also remove the newly explicit keyword from implicit_interests
            # so it won't be present on the returned profile.
            if "implicit_interests" in profile and profile.get("implicit_interests"):
                profile["implicit_interests"] = {
                    k: v for k, v in profile["implicit_interests"].items()
                    if k.lower() != kw.lower()
                }

    profile["explicit_interests"] = list(keyword_map.values())

    user_profiles_col.update_one(
        {"user_id": effective_user},
        {"$set": profile},
        upsert=True
    )
    logger.info("Bulk explicit interests updated", extra={
        "user_id": effective_user,
        "update_count": len(updates)
    })

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
    logger.info("Explicit interest removed", extra={
        "user_id": effective_user,
        "keyword": keyword
    })

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


@router.delete("/profiles/implicit/exclusion/remove")
async def remove_implicit_exclusion(
        user_id: str = Body(None),
        keyword: str = Body(...),
        auth_user: str = Depends(get_user_id_from_auth)
):
    """Remove a keyword from implicit exclusions (undo an exclusion)"""
    effective_user = (
        auth_user if auth_user and auth_user != "guest"
        else (user_id or "guest")
    )

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
