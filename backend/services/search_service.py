from services.google_api import search_google

def search(query: str):
    """
    Main search pipeline. Currently calls Google API directly.
    Later, can add:
      - query enhancement
      - personalization
      - post-processing/ranking
    """
    return search_google(query)
