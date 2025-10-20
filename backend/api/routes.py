from fastapi import APIRouter, Query
from services.search_service import search  # absolute import

router = APIRouter()

@router.get("/search")
async def search_endpoint(q: str = Query(..., description="Search query")):
    try:
        results = search(q)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}
