from fastapi import APIRouter, Query, Body, HTTPException
from services.search_service import search
from services.logging_service import log_query, log_interaction
from services.user_profile_service import build_user_profile
from services.db import user_profiles_col
from datetime import datetime

router = APIRouter()

# ----- Search endpoints -----
@router.get("/search")
async def search_endpoint(q: str = Query(...), user_id: str = "guest"):
    query_id = log_query(user_id=user_id, raw_text=q)
    results = search(q)
    return {"query_id": query_id, "results": results}

@router.post("/interactions")
async def log_click(user_id: str = Body(...), query_id: str = Body(...),
                    clicked_url: str = Body(...), rank: int = Body(...)):
    interaction_id = log_interaction(user_id, query_id, clicked_url, rank)
    return {"interaction_id": interaction_id, "status": "logged"}

# ----- User profile endpoints -----
@router.get("/profiles/{user_id}")
async def get_user_profile(user_id: str):
    profile = build_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile

@router.post("/profiles/explicit/add")
async def add_explicit_interest(user_id: str = Body(...), keyword: str = Body(...), weight: float = Body(1.0)):
    profile = build_user_profile(user_id)
    for e in profile["explicit_interests"]:
        if e["keyword"].lower() == keyword.lower():
            raise HTTPException(status_code=400, detail="Keyword already exists")
    profile["explicit_interests"].append({
        "keyword": keyword,
        "weight": weight,
        "last_updated": datetime.utcnow().isoformat()
    })
    user_profiles_col.update_one({"user_id": user_id}, {"$set": profile}, upsert=True)
    return profile

@router.put("/profiles/explicit/bulk_update")
async def bulk_update_explicit_interests(user_id: str = Body(...), updates: list = Body(...)):
    """
    BULK UPDATE: updates all explicit interests in a single request.
    This reduces lag by avoiding multiple PUT requests per slider change.
    Each item in `updates` is expected to be {"keyword": str, "weight": float}.
    """
    profile = build_user_profile(user_id)
    keyword_map = {e["keyword"].lower(): e for e in profile["explicit_interests"]}

    for item in updates:
        kw = item["keyword"]
        wt = float(item.get("weight", 1.0))
        if kw.lower() in keyword_map:
            keyword_map[kw.lower()]["weight"] = wt
            keyword_map[kw.lower()]["last_updated"] = datetime.utcnow().isoformat()
        else:
            # new interest (shouldn't happen normally in bulk)
            profile["explicit_interests"].append({
                "keyword": kw,
                "weight": wt,
                "last_updated": datetime.utcnow().isoformat()
            })

    profile["explicit_interests"] = list(keyword_map.values())
    user_profiles_col.update_one({"user_id": user_id}, {"$set": profile}, upsert=True)
    return profile

@router.delete("/profiles/explicit/remove")
async def remove_explicit_interest(user_id: str = Body(...), keyword: str = Body(...)):
    profile = build_user_profile(user_id)
    profile["explicit_interests"] = [e for e in profile["explicit_interests"] if e["keyword"].lower() != keyword.lower()]
    user_profiles_col.update_one({"user_id": user_id}, {"$set": profile}, upsert=True)
    return profile

@router.delete("/profiles/implicit/remove")
async def remove_implicit_interest(user_id: str = Body(...), keyword: str = Body(...)):
    """
    Persistently suppress an implicit interest for this user by adding the keyword
    to `implicit_exclusions`. Then rebuild the profile and return it.
    """
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword required")

    existing_profile = user_profiles_col.find_one({"user_id": user_id}) or {}
    exclusions = existing_profile.get("implicit_exclusions", [])

    # Add case-insensitively
    if keyword.lower() not in [e.lower() for e in exclusions]:
        exclusions.append(keyword)
        user_profiles_col.update_one({"user_id": user_id}, {"$set": {"implicit_exclusions": exclusions}}, upsert=True)

    # TODO: ensure future personalization algorithm excludes implicit_exclusions
    # Rebuild profile (which will filter out exclusions)
    profile = build_user_profile(user_id)
    return profile
