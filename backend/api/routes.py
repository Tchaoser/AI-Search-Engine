from fastapi import APIRouter
from services.google_api import search_google

router = APIRouter()

@router.get("/search")
async def search(q: str):
    try:
        results = search_google(q, num_results=5)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}
