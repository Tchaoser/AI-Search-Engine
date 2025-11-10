from fastapi import APIRouter, Query, Body, Depends
from services.search_service import search
from services.logging_service import log_query, log_interaction
from services import auth_service

router = APIRouter()

# ---- Reuse auth helper ----
from api.utils import get_user_id_from_auth

# ---- Search endpoints ----
@router.get("/search")
async def search_endpoint(q: str = Query(...), user_id: str = Depends(get_user_id_from_auth)):
    query_id = log_query(user_id=user_id, raw_text=q)
    results = search(q)
    return {"query_id": query_id, "results": results}

@router.post("/interactions")
async def log_click(user_id: str = Body(None), query_id: str = Body(...),
                    clicked_url: str = Body(...), rank: int = Body(...),
                    auth_user: str = Depends(get_user_id_from_auth)):
    effective_user = auth_user if auth_user and auth_user != "guest" else (user_id or "guest")
    interaction_id = log_interaction(effective_user, query_id, clicked_url, rank)
    return {"interaction_id": interaction_id, "status": "logged"}
