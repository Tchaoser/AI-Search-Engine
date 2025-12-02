from services.db import queries_col, interactions_col
from models.data_models import make_query_doc, make_interaction_doc
from services.logger import AppLogger

logger = AppLogger.get_logger(__name__)


def log_query(user_id: str, raw_text: str, enhanced_text: str = None):
    """
    Create a query document and insert it into MongoDB.
    
    Returns the inserted document's ID.
    """
    try:
        doc = make_query_doc(user_id, raw_text, enhanced_text)
        queries_col.insert_one(doc)
        logger.debug("Query document inserted", extra={
            "user_id": user_id,
            "query_id": doc["_id"],
            "raw_text_length": len(raw_text)
        })
        return doc["_id"]
    except Exception as e:
        logger.error("Failed to log query", extra={
            "user_id": user_id,
            "error": str(e)
        }, exc_info=True)
        raise


def log_interaction(user_id: str, query_id: str, clicked_url: str, rank: int, action_type: str = "click"):
    """
    Log a user interaction (click) in MongoDB:
      - Clicks:          action_type="click"
      - :       action_type="feedback_positive"
      - –:       action_type="feedback_negative"
    """
    try:
        doc = make_interaction_doc(user_id, query_id, clicked_url, rank)
        interactions_col.insert_one(doc)
        logger.debug("Interaction document inserted", extra={
            "user_id": user_id,
            "interaction_id": doc["_id"],
            "query_id": query_id,
            "rank": rank
        })
        return doc["_id"]
    except Exception as e:
        logger.error("Failed to log interaction", extra={
            "user_id": user_id,
            "query_id": query_id,
            "error": str(e)
        }, exc_info=True)
        raise


def log_feedback(user_id: str, query_id: str, result_url: str, rank: int, is_positive: bool):
    """
    Log explicit relevance feedback in MongoDB.

    action_type:
      - "positive_feedback" when is_positive is True
      - "negative_feedback" when is_positive is False
    """
    action_type = "positive_feedback" if is_positive else "negative_feedback"

    try:
        interactions_col.delete_many({
            "user_id": user_id,
            "clicked_url": result_url,
            "action_type": {"$in": ["positive_feedback", "negative_feedback"]},
        })

        doc = make_interaction_doc(
            user_id=user_id,
            query_id=query_id,
            clicked_url=result_url,
            rank=rank,
            action_type=action_type,
        )
        interactions_col.insert_one(doc)
        logger.debug("Feedback document inserted", extra={
            "user_id": user_id,
            "feedback_id": doc["_id"],
            "query_id": query_id,
            "rank": rank,
            "action_type": action_type,
        })
        return doc["_id"]
    except Exception as e:
        logger.error("Failed to log feedback", extra={
            "user_id": user_id,
            "query_id": query_id,
            "action_type": action_type,
            "error": str(e),
        }, exc_info=True)
        raise