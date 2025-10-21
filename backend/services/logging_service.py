from services.db import queries_col
from models.data_models import make_query_doc

def log_query(user_id: str, raw_text: str, enhanced_text: str = None):
    """
    Create a query document and insert it into MongoDB.
    Returns the inserted document's ID.
    """
    try:
        doc = make_query_doc(user_id, raw_text, enhanced_text)
        queries_col.insert_one(doc)
        return doc["_id"]
    except Exception as e:
        print(f"[log_query] Failed: {e}")
        return None
