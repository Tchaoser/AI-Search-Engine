from services.google_api import search_google
from services.user_profile_service import preprocess, normalize_url
from services.db import user_profiles_col


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
    explicit = {e["keyword"].lower(): e.get("weight", 1.0) for e in (profile.get("explicit_interests", []) if profile else [])}

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
    Search pipeline: proxies to Google Custom Search, then applies personalization/reranking
    using the user's cached profile if available.
    
    Returns a list of results ordered by personalized score.
    """
    results = search_google(query)

    # If no user_id provided, skip personalization
    if not user_id:
        return results

    # Fetch cached profile from DB (no rebuild to reduce overhead)
    try:
        profile = user_profiles_col.find_one({"user_id": user_id})
    except Exception:
        profile = None

    if not profile:
        return results

    # Assign base rank score (higher for earlier results)
    scored = []
    for idx, r in enumerate(results):
        # base positional score: inverse of rank (1-based)
        pos_score = max(0.0, (len(results) - idx)) / max(1.0, len(results))
        personal_score = _score_result(r, profile)
        total = pos_score + personal_score
        scored.append((total, r))

    # sort by total descending
    scored.sort(key=lambda x: -x[0])
    return [r for (_s, r) in scored]
