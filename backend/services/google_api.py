import os
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env into environment

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

if not GOOGLE_API_KEY or not GOOGLE_CX:
    raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_CX in environment variables (.env)")

def search_google(query: str, num_results: int = 5):
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": num_results,
    }
    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
        })
    return results
