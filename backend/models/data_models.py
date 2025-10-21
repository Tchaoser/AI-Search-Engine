import uuid
from datetime import datetime

def make_query_doc(user_id: str, raw_text: str, enhanced_text: str = None, session_id: str = None):
    """
    Prepare a query document for insertion into MongoDB.
    """
    return {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "raw_text": raw_text,
        "enhanced_text": enhanced_text,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
    }
