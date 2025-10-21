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
    } # Other info like session_id can be added later as required
