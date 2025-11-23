import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "ai_search_dev")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections (simple handles)
queries_col = db["queries"]
interactions_col = db["interactions"]
user_profiles_col = db["user_profiles"]
users_col = db["users"]
# Collection to track tokens that were discarded during preprocessing
discarded_tokens_col = db["discarded_tokens"]