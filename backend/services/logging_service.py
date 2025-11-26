from services.db import queries_col, interactions_col
from models.data_models import make_query_doc, make_interaction_doc


def log_query(user_id: str, raw_text: str, enhanced_text: str = None):
    """
    Create a query document and insert it into MongoDB.
    
    Returns the inserted document's ID.
    """
    doc = make_query_doc(user_id, raw_text, enhanced_text)
    queries_col.insert_one(doc)
    return doc["_id"]


def log_interaction(user_id: str, query_id: str, clicked_url: str, rank: int):
    """
    Log a user interaction (click) in MongoDB.
    """
    doc = make_interaction_doc(user_id, query_id, clicked_url, rank)
    interactions_col.insert_one(doc)
    return doc["_id"]

