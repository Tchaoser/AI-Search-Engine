from services.db import queries_col, interactions_col
from models.data_models import make_query_doc, make_interaction_doc
from services.user_profile_service import build_user_profile


def log_query(user_id: str, raw_text: str, enhanced_text: str = None):
    """
    Create a query document and insert it into MongoDB.
    Rebuilds the user's profile after inserting the query to ensure
    session patterns are reflected quickly.

    Returns the inserted document's ID.
    """
    doc = make_query_doc(user_id, raw_text, enhanced_text)
    queries_col.insert_one(doc)

    # Recompute profile to capture this new query (synchronous for now).
    try:
        build_user_profile(user_id)
    except Exception:
        # don't let profile rebuild failures break logging; callers should still get a query_id
        pass

    return doc["_id"]


def log_interaction(user_id: str, query_id: str, clicked_url: str, rank: int):
    """
    Log a user interaction (click) in MongoDB and rebuild the profile so
    clicks immediately influence the user's implicit interests.
    """
    doc = make_interaction_doc(user_id, query_id, clicked_url, rank)
    interactions_col.insert_one(doc)

    # Recompute profile to capture this new interaction (synchronous for now).
    try:
        build_user_profile(user_id)
    except Exception:
        pass

    return doc["_id"]
