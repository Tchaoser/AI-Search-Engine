import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.user_profile_service import build_user_profile
from services.db import queries_col
def run_profile_build():
    """
    Aggregates all unique user_ids in queries_col and rebuilds their profiles.
    Explicit interests are preserved.
    """
    user_ids = queries_col.distinct("user_id")
    print(f"Found {len(user_ids)} users: {user_ids}")

    for uid in user_ids:
        print(f"\n🔄 Building profile for user: {uid}")
        profile = build_user_profile(uid)  # preserves explicit_interests
        print(f"✅ Updated profile for {uid} with {len(profile['implicit_interests'])} implicit interests")
        print(f"   {list(profile['implicit_interests'].items())[:8]} ...")

    print("\n🏁 Done building all user profiles.")

if __name__ == "__main__":
    run_profile_build()
