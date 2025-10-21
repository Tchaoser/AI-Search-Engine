from fastapi import APIRouter, Query
from services.search_service import search
from models.data_models import make_query_doc
from services.db import queries_col  # your MongoDB collection handle

router = APIRouter()

@router.get("/search")
async def search_endpoint(q: str = Query(..., description="Search query"), user_id: str = "guest"):
    """
    Search endpoint: logs query in MongoDB, then returns results from Google.
    """
    # 1. Log the query
    query_doc = make_query_doc(user_id=user_id, raw_text=q)
    try:
        queries_col.insert_one(query_doc)
        query_id = query_doc["_id"]
    except Exception as e:
        print(f"Failed to log query: {e}")
        query_id = None

    # 2. Run search
    try:
        results = search(q)
        return {"query_id": query_id, "results": results}
    except Exception as e:
        return {"query_id": query_id, "results": [], "error": str(e)}
