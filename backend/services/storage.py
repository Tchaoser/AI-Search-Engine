# backend/services/storage.py
import os
import datetime as dt
from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "ai_search_dev")
MONGO_COLL_QUERIES = os.getenv("MONGO_COLL_QUERIES", "enhanced_text")

_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB]
_logs = _db[MONGO_COLL_QUERIES]

# Helpful indexes (safe to run even if collection exists)
_logs.create_index([("created_at", ASCENDING)])
_logs.create_index([("user_id", ASCENDING)], sparse=True)

async def log_query(
    *,
    original_text: str,
    enhanced_text: str,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
):
    """
    Persist the query pair so we can inspect later or do analytics.

    Args:
        original_text: What user typed.
        enhanced_text: Expanded query sent to search.
        user_id: Optional app user id if available.
        extra: Optional dict to attach (ip, session_id, flags, etc.)
    """
    doc = {
        "original_text": original_text,
        "enhanced_text": enhanced_text,
        "user_id": user_id,
        "created_at": dt.datetime.utcnow(),
    }
    if extra:
        doc.update(extra)
    _logs.insert_one(doc)
