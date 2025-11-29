"""
Before running, ask: do you need this script?

You need this script if:
    ✔ Your stored profiles get out of sync
    ✔ You want to batch-rebuild all user profiles based on their historical queries
    ✔ You want to test the output of build_user_profile on all users
    ✔ You run it as a maintenance job

You do not need it if:
    ✘ You always compute profiles dynamically through the API
    ✘ You don’t store implicit interests permanently
    ✘ You don’t need batch regeneration
    ✘ Profiles are up-to-date automatically through interactions
"""
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
