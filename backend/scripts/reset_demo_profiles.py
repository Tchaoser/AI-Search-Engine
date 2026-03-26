from datetime import datetime, timezone

from services.db import queries_col, interactions_col, user_profiles_col


def reset_user_profile(user_id: str, explicit_keywords: list[str]):
    # 1. Remove past queries & interactions
    queries_col.delete_many({"user_id": user_id})
    interactions_col.delete_many({"user_id": user_id})

    # 2. Reset profile
    profile_doc = {
        "user_id": user_id,
        "explicit_interests": [{"keyword": kw, "weight": 1.0} for kw in explicit_keywords],
        "implicit_interests": {},
        "query_history": [],
        "click_history": [],
        "implicit_exclusions": [],
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "profile_revision": 1,
        "embedding": None
    }

    # 3. Upsert into Mongo
    user_profiles_col.update_one(
        {"user_id": user_id},
        {"$set": profile_doc},
        upsert=True
    )

# Developer
reset_user_profile(
    "Developer User",
    ["programming", "web development", "APIs"]
)

# Tech Investor
reset_user_profile(
    "Tech Investor User",
    ["stock market", "tech companies", "cryptocurrency"]
)

# Fitness User
reset_user_profile(
    "Fitness User",
    ["fitness", "weightlifting", "nutrition"]
)

# Student / Productivity
reset_user_profile(
    "Student User",
    ["studying", "productivity", "time management"]
)