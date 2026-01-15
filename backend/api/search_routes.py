import time
from fastapi import APIRouter, Query, Body, Depends, HTTPException
from services.search_service import search
from services.logging_service import log_query, log_interaction, log_feedback
from services.semantic_expansion import expand_query
from services.logger import AppLogger
from api.utils import get_user_id_from_auth

router = APIRouter()
logger = AppLogger.get_logger(__name__)


@router.get("/search")
async def search_endpoint(
        q: str = Query(...),
        use_enhanced: bool = Query(True),
        verbosity: str = Query("medium"),
        semantic_mode: str = Query("clarify_only"),
        user_id: str = Depends(get_user_id_from_auth)
):
    """
    Search endpoint with optional semantic expansion.

    Behavior:
      - If use_enhanced=True, attempt semantic expansion using an LLM.
      - Personalization snippet can be included based on user profile and verbosity.
      - If expansion fails or use_enhanced=False, fall back to original query.

    Parameters:
      q: str
        The raw search query entered by the user.
      use_enhanced: bool
        Whether to apply semantic expansion (defaults to True).
      verbosity: str
        How strongly personalization is applied (defaults to 'medium').
        Possible values:
          - off      → no personalization snippet
          - low      → strong interests only
          - medium   → strong + medium
          - high     → all available interests
      semantic_mode: str
        Determines how ambiguous queries are handled (defaults to 'clarify_only').
        Possible values:
          - clarify_only             → conservative expansion, never uses user interests to resolve ambiguity
          - clarify_and_personalize  → uses strong user interests to resolve ambiguity when present
      user_id: str (from Depends)
        Authenticated user ID; guest if not logged in.

    Returns:
      JSON object with:
        - query_id
        - results (list)
        - original_query
        - enhanced_query
        - use_enhanced
        - verbosity
    """
    start_time = time.time()

    # Log initial request
    logger.info("Search request received", extra={
        "user_id": user_id,
        "query": q,
        "use_enhanced": use_enhanced,
        "verbosity": verbosity,
        "semantic mode": semantic_mode
    })

    if use_enhanced:
        # Pass user_id, verbosity, and semantic_mode for personalized semantic expansion
        enhanced = await expand_query(
            q,
            user_id=user_id,
            verbosity=verbosity,
            semantic_mode=semantic_mode,
        )

        if enhanced != q:
            logger.debug("Query expanded", extra={
                "original": q,
                "expanded": enhanced
            })
    else:
        enhanced = q
        logger.debug("Query expansion disabled", extra={"query": q})

    # Log the query in DB before search (helps personalization/reranking)
    query_id = log_query(
        user_id=user_id,
        raw_text=q,
        enhanced_text=enhanced
    )
    logger.debug("Query logged to database", extra={
        "user_id": user_id,
        "query_id": query_id
    })

    # Perform search using the active query
    results = search(enhanced, user_id=user_id)

    # Measure duration
    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    logger.info("Search completed", extra={
        "user_id": user_id,
        "result_count": len(results),
        "duration_ms": elapsed_ms,
        "use_enhanced": use_enhanced,
        "verbosity": verbosity,
        "semantic mode": semantic_mode
    })

    return {
        "query_id": query_id,
        "results": results,
        "original_query": q,
        "enhanced_query": enhanced,
        "use_enhanced": use_enhanced,
        "verbosity": verbosity,
        "semantic mode": semantic_mode
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
    logger.info("Click logged", extra={
        "user_id": effective_user,
        "query_id": query_id,
        "url": clicked_url,
        "rank": rank
    })

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


@router.post("/feedback")
async def log_feedback_endpoint(
        user_id: str = Body(None),
        query_id: str = Body(...),
        result_url: str = Body(...),
        rank: int = Body(...),
        is_relevant: bool = Body(...),
        auth_user: str = Depends(get_user_id_from_auth),
):
    """
    Record explicit relevance feedback for a specific search result.

    This is stored in the interactions collection as:
      action_type = "positive_feedback" if is_relevant  else "negative_feedback"
    """
    effective_user = (
        auth_user
        if auth_user and auth_user != "guest"
        else (user_id or "guest")
    )

    logger.info("Logging relevance feedback", extra={
        "user_id": effective_user,
        "query_id": query_id,
        "result_url": result_url,
        "rank": rank,
        "is_relevant": is_relevant,
    })

    feedback_id = log_feedback(
        effective_user,
        query_id,
        result_url,
        rank,
        is_positive=is_relevant,
    )

    return {
        "feedback_id": feedback_id,
        "status": "logged",
    }
