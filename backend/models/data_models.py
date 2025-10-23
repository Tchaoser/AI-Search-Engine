import uuid
from datetime import datetime

def make_query_doc(user_id: str, raw_text: str, enhanced_text: str = None):
    """
    Prepare a query document for insertion into MongoDB.
    """
    return {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "raw_text": raw_text,
        "enhanced_text": enhanced_text,
        "timestamp": datetime.utcnow().isoformat(),
    }

def make_interaction_doc(user_id: str, query_id: str, clicked_url: str, rank: int):
    """
    Prepare an interaction document for insertion into MongoDB.
    """
    return {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "query_id": query_id,
        "clicked_url": clicked_url,
        "rank": rank,
        "timestamp": datetime.utcnow().isoformat(),
        "action_type": "click",
    }
