import os
from dotenv import load_dotenv
from pymongo import MongoClient
from backend.services.logger import AppLogger

logger = AppLogger.get_logger(__name__)

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "ai_search_dev")

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    logger.info("Database connection established", extra={"db_name": DB_NAME})
except Exception as e:
    logger.error("Failed to connect to database", extra={
        "db_name": DB_NAME,
        "error": str(e)
    }, exc_info=True)
    raise

# Collections (simple handles)
queries_col = db["queries"]
interactions_col = db["interactions"]
user_profiles_col = db["user_profiles"]
users_col = db["users"]
# Collection to track tokens that were discarded during preprocessing
discarded_tokens_col = db["discarded_tokens"]
# Collection to store benchmark result snapshots
benchmark_results_col = db["benchmark_results"]
# Collection to store evaluator relevance judgments
relevance_judgments_col = db["relevance_judgments"]

logger.debug("Database collections initialized", extra={
    "collections": ["queries", "interactions", "user_profiles", "users", "discarded_tokens", "benchmark_results", "relevance_judgments"]
})