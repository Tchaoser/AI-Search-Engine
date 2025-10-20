import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Loads GOOGLE_API_KEY and GOOGLE_CX from .env

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

if not GOOGLE_API_KEY or not GOOGLE_CX:
    raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_CX in environment variables.")

def search_google(query: str, num_results: int = 5):
    """
    Calls Google Custom Search API and returns simplified results.
    """
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": num_results,
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
        })
    return results
