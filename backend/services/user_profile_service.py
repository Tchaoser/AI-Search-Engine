from collections import Counter, defaultdict
from datetime import datetime
import re
from urllib.parse import urlparse
from services.db import queries_col, interactions_col, user_profiles_col

STOP_WORDS = {"the", "and", "of", "a", "to", "in", "for", "on", "with"}

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return [t for t in text.split() if t not in STOP_WORDS]

def aggregate_queries(user_id):
    docs = list(queries_col.find({"user_id": user_id}))
    tokens = []
    for q in docs:
        tokens.extend(preprocess(q.get("raw_text", "")))
    return dict(Counter(tokens))

def normalize_url(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path_parts = [p for p in parsed.path.split("/") if p]
    if path_parts:
        top_path = path_parts[0]
        return f"{domain}/{top_path}"
    return domain

def aggregate_clicks(user_id):
    docs = list(interactions_col.find({"user_id": user_id}))
    domain_counts = defaultdict(float)
    n_docs = len(docs)
    if n_docs == 0:
        return {}

    for doc in docs:
        domain = normalize_url(doc.get("clicked_url", ""))
        rank = doc.get("rank", 1)
        # Apply a soft rank weight: higher rank → slightly higher weight
        weight = max(1.0, (10 - rank) / 10.0)  # rank 1 → 0.9, rank 10 → 0.0
        domain_counts[domain] += weight

    return dict(domain_counts)

def build_user_profile(user_id, query_weight=1.0, click_weight=2.0):
    keywords = aggregate_queries(user_id)
    clicks = aggregate_clicks(user_id)

    interests = {}
    for k, v in keywords.items():
        interests[k] = v * query_weight
    for domain, v in clicks.items():
        interests[domain] = interests.get(domain, 0) + v * click_weight

    existing_profile = user_profiles_col.find_one({"user_id": user_id}) or {}
    explicit_interests = existing_profile.get("explicit_interests", [])
    # read implicit exclusions (list of keywords to hide)
    implicit_exclusions_raw = existing_profile.get("implicit_exclusions", [])
    implicit_exclusions = set([e.lower() for e in implicit_exclusions_raw])

    # filter out excluded implicit interests (case-insensitive)
    filtered_interests = {k: v for k, v in interests.items() if k.lower() not in implicit_exclusions}

    profile_doc = {
        "user_id": user_id,
        "interests": filtered_interests,
        "query_history": list(keywords.keys()),
        "click_history": list(clicks.keys()),
        "last_updated": datetime.utcnow().isoformat(),
        "explicit_interests": explicit_interests,
        "implicit_exclusions": implicit_exclusions_raw,
        "embedding": None
    }

    user_profiles_col.update_one(
        {"user_id": user_id},
        {"$set": profile_doc},
        upsert=True
    )
    return profile_doc

