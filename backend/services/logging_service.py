from datetime import datetime
import uuid
from services.db import queries_col

def make_query_doc(user_id: str, raw_text: str, enhanced_text: str = None):
    return {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "raw_text": raw_text,
        "enhanced_text": enhanced_text,
        "timestamp": datetime.utcnow().isoformat(),
    }

def log_query(user_id: str, raw_text: str, enhanced_text: str = None):
    try:
        doc = make_query_doc(user_id, raw_text, enhanced_text)
        queries_col.insert_one(doc)
        return doc["_id"]
    except Exception as e:
        print(f"[log_query] Failed: {e}")
        return None
