import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re
import math
from urllib.parse import urlparse
from services.db import queries_col, interactions_col, user_profiles_col, discarded_tokens_col

# Session decay: interactions within this window get a boost multiplier
# Default: 480 minutes = 8 hours
SESSION_DECAY_MINUTES = int(os.getenv("SESSION_DECAY_MINUTES", 480))
SESSION_BOOST_MULTIPLIER = float(os.getenv("SESSION_BOOST_MULTIPLIER", 1.5))

# Expanded stopword list (common English stopwords + some domain-specific tokens)
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "is", "are", "was", "were",
    "be", "been", "being", "in", "on", "at", "of", "for", "to", "from", "by", "with", "about",
    "into", "through", "after", "before", "over", "under", "it", "its", "they", "them", "he",
    "she", "you", "your", "i", "me", "my", "we", "our", "ours", "their", "theirs", "this",
    "that", "these", "those", "as", "so", "too", "very", "just", "can", "will", "would", "should",
    "do", "does", "did", "done", "not", "no", "yes", "what", "which", "who", "whom", "where",
    "when", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "only", "own", "same", "than", "then", "also", "here", "there", "been", "per", "via",
    # domain-specific / low-value tokens often seen in queries
    "search", "query", "queries", "result", "results", "page", "pages", "link", "links", "click",
    "clicks", "test", "example", "info", "information", "article", "articles", "howto", "tutorial",
    "http", "https", "www", "com", "org", "net", "io", "gov", "edu", "amp", "amphtml"
}


def preprocess(text: str, discarded_counter: Counter = None):
    """
    Clean and tokenize a query string.

    - Lowercase, remove punctuation.
    - Remove stopwords, numeric-only tokens, and tokens shorter than 2 chars.
    - Optionally increments discarded_counter for tokens removed (for later analysis).
    """
    if not text:
        return []
    text = text.lower()
    # remove punctuation (keep unicode word characters)
    text = re.sub(r"[^\w\s]", " ", text)
    raw_tokens = [t.strip() for t in text.split() if t.strip()]

    out = []
    for t in raw_tokens:
        # normalize common URL artifacts
        if t.startswith("http"):
            # skip raw urls in query tokens
            if discarded_counter is not None:
                discarded_counter[t] += 1
            continue
        # discard numeric-only tokens
        if t.isdigit():
            if discarded_counter is not None:
                discarded_counter[t] += 1
            continue
        # discard tokens shorter than 2
        if len(t) < 2:
            if discarded_counter is not None:
                discarded_counter[t] += 1
            continue
        # discard stopwords
        if t in STOP_WORDS:
            if discarded_counter is not None:
                discarded_counter[t] += 1
            continue
        out.append(t)
    return out


def normalize_url(url: str) -> str:
    parsed = urlparse(url or "")
    domain = parsed.netloc.replace("www.", "")
    path_parts = [p for p in parsed.path.split("/") if p]
    if path_parts:
        top_path = path_parts[0]
        return f"{domain}/{top_path}"
    return domain or url


def _parse_iso(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.utcnow()


def aggregate_queries(user_id: str,
                      session_window_minutes: int = 30,
                      recency_decay_days: float = 30.0,
                      session_decay_minutes: int = None,
                      discarded_counter: Counter = None):
    """
    Aggregate and score tokens from user's past queries.

    - Groups queries into sessions using session_window_minutes.
    - Applies recency decay (exponential) based on recency_decay_days.
    - Applies a session boost when tokens appear in the current session (within session_decay_minutes).
    - Applies a session boost when tokens are repeated within a session.
    Returns a dict[token] -> score and list of unique tokens (for history).
    """
    if session_decay_minutes is None:
        session_decay_minutes = SESSION_DECAY_MINUTES
    
    docs = list(queries_col.find({"user_id": user_id}))
    if not docs:
        return {}, []

    # sort by timestamp
    docs_sorted = sorted(docs, key=lambda d: d.get("timestamp", ""))

    # build sessions
    sessions = []  # list of list of (tokens, ts)
    current_session = []
    last_ts = None
    for doc in docs_sorted:
        ts = _parse_iso(doc.get("timestamp", datetime.utcnow().isoformat()))
        if last_ts is None:
            current_session = [(doc, ts)]
        else:
            gap = (ts - last_ts).total_seconds() / 60.0
            if gap <= session_window_minutes:
                current_session.append((doc, ts))
            else:
                sessions.append(current_session)
                current_session = [(doc, ts)]
        last_ts = ts
    if current_session:
        sessions.append(current_session)

    token_scores = defaultdict(float)
    token_seen = set()
    now = datetime.utcnow()
    session_cutoff = now - timedelta(minutes=session_decay_minutes)

    for session in sessions:
        # collect per-session counts
        session_counter = Counter()
        # session recency mean (use average of contained queries)
        session_age_days = 0.0
        for doc, ts in session:
            qs = preprocess(doc.get("raw_text", ""), discarded_counter)
            for t in qs:
                session_counter[t] += 1
            session_age_days += (now - ts).total_seconds() / 86400.0
        if len(session) > 0:
            session_age_days /= len(session)

        # recency multiplier (exponential decay)
        recency_mult = math.exp(- (session_age_days / max(1.0, recency_decay_days)))
        
        # check if session is within SESSION_DECAY_MINUTES (current session window)
        session_ts = session[-1][1]  # use last query in session as reference
        in_current_session = session_ts >= session_cutoff
        session_mult = SESSION_BOOST_MULTIPLIER if in_current_session else 1.0

        # apply per-token scoring within the session
        for token, cnt in session_counter.items():
            # session boost if repeated within session
            s_boost = 1.0 + (0.5 * (cnt - 1)) if cnt > 1 else 1.0
            token_scores[token] += cnt * s_boost * recency_mult * session_mult
            token_seen.add(token)

    return dict(token_scores), list(token_seen)


def aggregate_clicks(user_id: str, recency_decay_days: float = 30.0, session_decay_minutes: int = None):
    """Aggregate and score clicked domains with recency and session weighting."""
    if session_decay_minutes is None:
        session_decay_minutes = SESSION_DECAY_MINUTES
    
    docs = list(interactions_col.find({"user_id": user_id}))
    domain_counts = defaultdict(float)
    if not docs:
        return {}

    now = datetime.utcnow()
    session_cutoff = now - timedelta(minutes=session_decay_minutes)
    
    for doc in docs:
        domain = normalize_url(doc.get("clicked_url", ""))
        rank = doc.get("rank", 1) or 1
        ts = _parse_iso(doc.get("timestamp", datetime.utcnow().isoformat()))
        age_days = (now - ts).total_seconds() / 86400.0
        recency_mult = math.exp(- (age_days / max(1.0, recency_decay_days)))

        # Apply a soft rank weight: higher rank (1) => higher weight
        rank_weight = max(0.1, (11 - float(rank)) / 10.0)  # rank 1 -> 1.0, rank 10 -> 0.1
        
        # Apply session boost for recent clicks within SESSION_DECAY_MINUTES
        session_mult = SESSION_BOOST_MULTIPLIER if ts >= session_cutoff else 1.0

        domain_counts[domain] += rank_weight * recency_mult * session_mult

    return dict(domain_counts)


def build_user_profile(user_id: str,
                       query_weight: float = 1.0,
                       click_weight: float = 2.0,
                       session_window_minutes: int = 30,
                       session_boost: float = 1.5,
                       recency_decay_days: float = 30.0,
                       session_decay_minutes: int = None):
    """
    Build or update the user profile with improved preprocessing and weighting.
    
    Session-aware weighting: interactions within session_decay_minutes receive a boost multiplier.

    Returns the profile document saved in MongoDB.
    """
    if session_decay_minutes is None:
        session_decay_minutes = SESSION_DECAY_MINUTES
    
    discarded_counter = Counter()

    keywords_scores, query_history = aggregate_queries(
        user_id,
        session_window_minutes=session_window_minutes,
        recency_decay_days=recency_decay_days,
        session_decay_minutes=session_decay_minutes,
        discarded_counter=discarded_counter
    )

    clicks_scores = aggregate_clicks(user_id, recency_decay_days=recency_decay_days, session_decay_minutes=session_decay_minutes)

    # Merge with tunable weights
    interests = defaultdict(float)
    for k, v in keywords_scores.items():
        interests[k] += v * query_weight
    for domain, v in clicks_scores.items():
        interests[domain] += v * click_weight

    # read existing profile for explicit interests and exclusions
    existing_profile = user_profiles_col.find_one({"user_id": user_id}) or {}
    explicit_interests = existing_profile.get("explicit_interests", [])
    implicit_exclusions_raw = existing_profile.get("implicit_exclusions", [])
    implicit_exclusions = set([e.lower() for e in implicit_exclusions_raw])

    # filter out excluded implicit interests (case-insensitive)
    filtered_interests = {k: v for k, v in interests.items() if k.lower() not in implicit_exclusions}

    profile_doc = {
        "user_id": user_id,
        "implicit_interests": dict(sorted(filtered_interests.items(), key=lambda x: -x[1])),
        "query_history": query_history,
        "click_history": list(clicks_scores.keys()),
        "last_updated": datetime.utcnow().isoformat(),
        "explicit_interests": explicit_interests,
        "implicit_exclusions": implicit_exclusions_raw,
        "embedding": None
    }

    # Persist profile
    user_profiles_col.update_one({"user_id": user_id}, {"$set": profile_doc}, upsert=True)

    # Persist discarded tokens counts for later analysis
    now = datetime.utcnow().isoformat()
    for token, cnt in discarded_counter.items():
        if not token:
            continue
        discarded_tokens_col.update_one(
            {"token": token},
            {"$inc": {"count": int(cnt)}, "$set": {"last_seen": now}},
            upsert=True
        )

    return profile_doc

