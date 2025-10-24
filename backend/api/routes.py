from fastapi import APIRouter, Query, Body
from services.search_service import search
from services.logging_service import log_query, log_interaction
from services.user_profile_service import build_user_profile

router = APIRouter()

@router.get("/search")
async def search_endpoint(q: str = Query(..., description="Search query"),
                          user_id: str = "guest"):
    """
    Search endpoint: logs query in MongoDB, then returns results from Google.
    """
    query_id = log_query(user_id=user_id, raw_text=q)
    results = search(q)
    return {"query_id": query_id, "results": results}

@router.post("/interactions")
async def log_click(
    user_id: str = Body(...),
    query_id: str = Body(...),
    clicked_url: str = Body(...),
    rank: int = Body(...)
):
    """
    Log a click interaction for a search result.
    """
    interaction_id = log_interaction(user_id, query_id, clicked_url, rank)
    return {"interaction_id": interaction_id, "status": "logged"}

@router.get("/profiles/{user_id}")
async def get_user_profile(user_id: str):
    profile = build_user_profile(user_id)
    return profile

@router.post("/profiles/update")
async def update_user_profile(user_id: str = Body(...), explicit_interests: list = Body(...)):
    # fetch existing profile
    profile = build_user_profile(user_id)
    profile["explicit_interests"] = explicit_interests
    # update in MongoDB
    from services.db import user_profiles_col
    user_profiles_col.update_one(
        {"user_id": user_id},
        {"$set": profile},
        upsert=True
    )
    return profile
