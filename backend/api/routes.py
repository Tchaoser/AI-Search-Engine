from fastapi import APIRouter, Query
from services.search_service import search
from services.logging_service import log_query

router = APIRouter()

@router.get("/search")
async def search_endpoint(q: str = Query(..., description="Search query"),
                          user_id: str = "guest"):
    """
    Search endpoint: logs query in MongoDB, then returns results from Google.
    """
    # 1. Log the query
    query_id = log_query(user_id=user_id, raw_text=q)

    # 2. Run search
    results = search(q)
    return {"query_id": query_id, "results": results}
