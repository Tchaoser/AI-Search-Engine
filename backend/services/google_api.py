import os
import requests
from dotenv import load_dotenv
from services.logger import AppLogger

logger = AppLogger.get_logger(__name__)

load_dotenv()  # loads .env into environment

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
PROXY_URL = os.getenv("SECURE_PROXY_URL")

if not GOOGLE_API_KEY or not GOOGLE_CX:
    logger.critical("Missing required Google API credentials")
    raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_CX in environment variables (.env)")

# Google Custom Search returns presentation-optimized fields, not raw document metadata.
# There is no way to tell CSE not to truncate titles/snippets
def search_google(query: str, num_results: int = 10):
    if not PROXY_URL:
        logger.critical("Missing SECURE_PROXY_URL in environment")
        raise ValueError("SECURE_PROXY_URL must be set in .env")

    params = {
        "q": query,
        "num": num_results
    }

    try:
        logger.debug("Calling Secure Proxy", extra={
            "query": query,
            "num_results": num_results
        })
        # Call the proxy instead of Google directly
        resp = requests.get(f"{PROXY_URL}/search", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("items", [])
        logger.debug("Secure Proxy call successful", extra={
            "query": query,
            "result_count": len(results)
        })
        return results
    except requests.exceptions.RequestException as e:
        logger.error("Secure Proxy call failed", extra={
            "query": query,
            "error": str(e)
        }, exc_info=True)
        raise
