"""
Background tasks for profile rebuilding and maintenance.

Runs on a scheduled interval (default 3 minutes) to keep user profiles
up-to-date with session-aware weighting without blocking search requests.
"""

import os
import threading
import time
from datetime import datetime
from services.db import queries_col, user_profiles_col
from services.user_profile_service import build_user_profile
from services.logger import AppLogger

# Configuration
PROFILE_REBUILD_INTERVAL_MINUTES = int(os.getenv("PROFILE_REBUILD_INTERVAL_MINUTES", 3))
PROFILE_REBUILD_ENABLED = os.getenv("PROFILE_REBUILD_ENABLED", "true").lower() == "true"

# Get logger
logger = AppLogger.get_logger(__name__)


class ProfileRebuildThread(threading.Thread):
    """
    Background thread that periodically rebuilds user profiles.
    
    Runs on a schedule to keep profiles fresh with session-aware weighting,
    avoiding the need for expensive rebuilds during search requests.
    """
    
    def __init__(self, interval_minutes: int = PROFILE_REBUILD_INTERVAL_MINUTES):
        super().__init__(daemon=True)
        self.interval_seconds = interval_minutes * 60
        self.running = False
        self.name = "ProfileRebuildThread"
    
    def run(self):
        """Main thread loop: rebuild profiles at regular intervals."""
        logger.info("Profile rebuild thread started", extra={
            "interval_minutes": PROFILE_REBUILD_INTERVAL_MINUTES,
            "interval_seconds": self.interval_seconds
        })
        self.running = True
        
        while self.running:
            try:
                self._rebuild_all_profiles()
            except Exception as e:
                logger.error("Error during profile rebuild cycle", extra={
                    "error": str(e)
                }, exc_info=True)
            
            # Sleep in small increments so we can exit quickly if needed
            for _ in range(int(self.interval_seconds)):
                if not self.running:
                    break
                time.sleep(1)
    
    def _rebuild_all_profiles(self):
        """Rebuild profiles for all users with recent activity."""
        try:
            # Find all unique user IDs from queries_col
            user_ids = queries_col.distinct("user_id")
            
            if not user_ids:
                logger.debug("No users with queries found; skipping rebuild cycle")
                return
            
            logger.info("Profile rebuild cycle starting", extra={"user_count": len(user_ids)})
            start_time = datetime.utcnow()
            
            rebuilt_count = 0
            failed_count = 0
            for user_id in user_ids:
                try:
                    build_user_profile(user_id)
                    rebuilt_count += 1
                    logger.debug("User profile rebuilt", extra={"user_id": user_id})
                except Exception as e:
                    failed_count += 1
                    logger.warning("Failed to rebuild profile", extra={
                        "user_id": user_id,
                        "error": str(e)
                    }, exc_info=False)
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info("Profile rebuild cycle complete", extra={
                "total_users": len(user_ids),
                "rebuilt_count": rebuilt_count,
                "failed_count": failed_count,
                "duration_s": round(elapsed, 2)
            })
        
        except Exception as e:
            logger.error("Critical error in profile rebuild cycle", extra={
                "error": str(e)
            }, exc_info=True)
    
    def stop(self):
        """Stop the background thread gracefully."""
        logger.info("Stopping profile rebuild thread")
        self.running = False


# Global thread instance
_rebuild_thread = None


def start_background_tasks():
    """Start background tasks (called on FastAPI startup)."""
    global _rebuild_thread
    
    if not PROFILE_REBUILD_ENABLED:
        logger.info("Profile rebuild background task is disabled")
        return
    
    if _rebuild_thread is not None and _rebuild_thread.is_alive():
        logger.warning("Profile rebuild thread already running")
        return
    
    _rebuild_thread = ProfileRebuildThread(interval_minutes=PROFILE_REBUILD_INTERVAL_MINUTES)
    _rebuild_thread.start()
    logger.info("Background tasks started")


def stop_background_tasks():
    """Stop background tasks (called on FastAPI shutdown)."""
    global _rebuild_thread
    
    if _rebuild_thread is None:
        return
    
    _rebuild_thread.stop()
    _rebuild_thread.join(timeout=5)
    _rebuild_thread = None
    logger.info("Background tasks stopped")
