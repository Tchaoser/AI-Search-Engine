from backend.services.google_api import search_google
from backend.services.user_profile_service import preprocess, normalize_url
from backend.services.db import user_profiles_col
from backend.services.logger import AppLogger

logger = AppLogger.get_logger(__name__)

RERANK_TOP_N = 5  # only re-rank the top N Google results


def _score_result(result: dict, profile: dict):
    """
    Compute a simple relevance score for a result using the user's profile.
    - base score from result position / presence
    - add domain boost if domain appears in implicit interests
    - add token matches from title/snippet using implicit and explicit interests
    """
    base = 0.0
    # results coming from Google have no explicit rank here; caller will pass ordered list
    title = (result.get("title") or "").lower()
    snippet = (result.get("snippet") or "").lower()
    link = result.get("link") or ""

    # interpret profile interests
    implicit = profile.get("implicit_interests", {}) if profile else {}
    explicit = {
        e["keyword"].lower(): e.get("weight", 1.0)
        for e in (profile.get("explicit_interests", []) if profile else [])
    }

    # domain boost
    dom = normalize_url(link)
    base += float(implicit.get(dom, 0.0))
    base += float(explicit.get(dom.lower(), 0.0))

    # token boosts from title/snippet
    tokens = preprocess(title + " " + snippet)
    for t in tokens:
        base += float(implicit.get(t, 0.0))
        base += float(explicit.get(t.lower(), 0.0))

    return base


def search(query: str, user_id: str = None):
    """
    Search pipeline:
    - proxy to Google Custom Search
    - optionally re-rank ONLY the top N results using the user's profile
    """
    logger.debug("Search initiated", extra={
        "user_id": user_id,
        "query": query
    })

    results = search_google(query)
    logger.debug("Google API results received", extra={
        "query": query,
        "result_count": len(results)
    })

    # No personalization without a user
    if not user_id:
        logger.debug("Skipping personalization: no user_id", extra={"query": query})
        return results

    # Fetch cached profile from DB (no rebuild to reduce overhead)
    try:
        profile = user_profiles_col.find_one({"user_id": user_id})
    except Exception as e:
        logger.warning("Failed to fetch user profile", extra={
            "user_id": user_id,
            "error": str(e)
        })
        profile = None

    if not profile:
        logger.debug("No profile found, returning unranked results", extra={"user_id": user_id})
        return results

    # Split results into head (to rerank) and tail (leave untouched)
    head = results[:RERANK_TOP_N]
    tail = results[RERANK_TOP_N:]

    scored = []
    for idx, r in enumerate(head):
        # positional bias within head only
        pos_score = max(0.0, (len(head) - idx)) / max(1.0, len(head))
        personal_score = _score_result(r, profile)
        total = pos_score + personal_score
        scored.append((total, r))

    # sort by total descending
    scored.sort(key=lambda x: -x[0])
    reranked_head = [r for (_s, r) in scored]

    final_results = reranked_head + tail

    logger.debug("Top-N results re-ranked using user profile", extra={
        "user_id": user_id,
        "reranked_count": len(reranked_head),
        "total_results": len(final_results)
    })

    return final_results
