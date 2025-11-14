from fastapi import APIRouter, Query, Body, Depends
from services.search_service import search
from services.logging_service import log_query, log_interaction
from services.semantic_expansion import expand_query
from api.utils import get_user_id_from_auth

router = APIRouter()


@router.get("/search")
async def search_endpoint(
        q: str = Query(...),
        user_id: str = Depends(get_user_id_from_auth)
):
    # Expand semantically (falls back to original query if expansion fails)
    enhanced = await expand_query(q)

    # Perform search using the enhanced query
    results = search(enhanced)

    # Log both original and expanded forms
    query_id = log_query(
        user_id=user_id,
        raw_text=q,
        enhanced_text=enhanced
    )

    return {
        "query_id": query_id,
        "results": results
    }


@router.post("/interactions")
async def log_click(
        user_id: str = Body(None),
        query_id: str = Body(...),
        clicked_url: str = Body(...),
        rank: int = Body(...),
        auth_user: str = Depends(get_user_id_from_auth)
):
    # Prefer authenticated user if present; otherwise fall back to provided or guest
    effective_user = (
        auth_user
        if auth_user and auth_user != "guest"
        else (user_id or "guest")
    )

    interaction_id = log_interaction(
        effective_user,
        query_id,
        clicked_url,
        rank
    )

    return {
        "interaction_id": interaction_id,
        "status": "logged"
    }
