from fastapi import APIRouter, Query, Body, Depends
from services.search_service import search
from services.logging_service import log_query, log_interaction
from services.semantic_expansion import expand_query
from api.utils import get_user_id_from_auth

router = APIRouter()


@router.get("/search")
async def search_endpoint(
        q: str = Query(...),
        use_enhanced: bool = Query(True),
        user_id: str = Depends(get_user_id_from_auth)
):
    """
    Search endpoint with optional semantic expansion.
    - If use_enhanced=True, attempt semantic expansion.
    - If expansion fails or use_enhanced=False, fall back to original query.
    """

    if use_enhanced:
        enhanced = await expand_query(q)   # safe fallback is implemented inside expand_query
    else:
        enhanced = q

    # Log the query before search so the user's profile reflects the most recent
    # session activity and can influence personalized reranking.
    query_id = log_query(
        user_id=user_id,
        raw_text=q,
        enhanced_text=enhanced
    )

    # Perform search using whichever query is active, pass user_id for personalization
    results = search(enhanced, user_id=user_id)

    return {
        "query_id": query_id,
        "results": results,
        "original_query": q,
        "enhanced_query": enhanced,
        "use_enhanced": use_enhanced
    }


@router.post("/interactions")
async def log_click(
        user_id: str = Body(None),
        query_id: str = Body(...),
        clicked_url: str = Body(...),
        rank: int = Body(...),
        auth_user: str = Depends(get_user_id_from_auth)
):
    """
    Log search interactions/clicks.
    Authenticated user overrides the supplied user_id.
    """

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
