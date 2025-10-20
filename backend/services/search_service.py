from services.google_api import search_google

def search(query: str):
    """
    Search pipeline: currently proxies to Google Custom Search.
    Future: add query enhancement, ranking, caching, personalization here.
    """
    return search_google(query)
