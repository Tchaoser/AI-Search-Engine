from fastapi import APIRouter, Query, Body
from services.search_service import search
from services.logging_service import log_query, log_interaction

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
