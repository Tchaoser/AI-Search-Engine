import uuid
from datetime import datetime, timezone

def make_query_doc(user_id: str, raw_text: str, enhanced_text: str = None, benchmark_metadata: dict = None):
    """
    Prepare a query document for insertion into MongoDB.
    If benchmark_metadata is provided, it is stored alongside the query.
    """
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "raw_text": raw_text,
        "enhanced_text": enhanced_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if benchmark_metadata is not None:
        doc["benchmark_metadata"] = benchmark_metadata
    return doc

def make_interaction_doc(user_id: str, query_id: str, clicked_url: str, rank: int, action_type: str = "click"):
    """
    Prepare an interaction document for insertion into MongoDB.
    """
    return {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "query_id": query_id,
        "clicked_url": clicked_url,
        "rank": rank,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_type": action_type, #can be click (default), positive_feedback or negative_feedback
    }

def make_user_profile_doc(user_id, interests, query_history, click_history, explicit_interests=None):
    """
    Create a user profile document. Explicit interests are optional, default empty list.
    """
    return {
        "user_id": user_id,
        "implicit_interests": interests,
        "query_history": query_history,
        "click_history": click_history,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "explicit_interests": explicit_interests or [],
        "embedding": None
    }

def make_benchmark_result_doc(query_id: str, experiment_arm: str, results: list):
    """
    Snapshot the top 5 search results for a benchmark query.
    Each result entry contains rank, title, url, and snippet.
    """
    top_results = []
    for rank, r in enumerate(results[:5], start=1):
        top_results.append({
            "rank": rank,
            "title": r.get("title", ""),
            "url": r.get("link", ""),
            "snippet": r.get("snippet", ""),
        })
    return {
        "_id": str(uuid.uuid4()),
        "query_id": query_id,
        "experiment_arm": experiment_arm,
        "results": top_results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def make_relevance_judgment_doc(benchmark_result_id: str, evaluator_id: str, judgments: list):
    """
    Store relevance labels for a benchmark result's top 5 results.
    Each entry in judgments: {"rank": int, "relevant": bool}
    """
    return {
        "_id": str(uuid.uuid4()),
        "benchmark_result_id": benchmark_result_id,
        "evaluator_id": evaluator_id,
        "judgments": judgments,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
