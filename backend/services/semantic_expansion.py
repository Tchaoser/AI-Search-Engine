# backend/services/semantic_expansion.py
import os
import httpx
from services.query_cache import query_cache #singleton cache imported

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TEMP = float(os.getenv("OLLAMA_TEMP", "0.4"))


#modify this for better results
SYSTEM_PROMPT = (
    "You expand short user queries into a single, more detailed search query. "
    "Keep it one line, human-readable, and include helpful specifics (entities, "
    "synonyms/aliases in parentheses, dates/regions/formats, intent keywords). "
    "Return ONLY the expanded query—no extra commentary."
)

async def expand_query(seed: str) -> str:
    seed = (seed or "").strip()
    if not seed:
        return seed
    
    in_cache = query_cache.get(seed, OLLAMA_MODEL, OLLAMA_TEMP)
    if in_cache:
        # Cached expanded query returned
        print("Query is in cache")
        return in_cache
    else:
        print("Query not in cache")
    

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": OLLAMA_TEMP},
        "system": SYSTEM_PROMPT,
        "prompt": seed,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{OLLAMA_URL.rstrip('/')}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
        text = (data.get("response") or "").strip()
        expanded = " ".join(text.split()) or seed
        #return " ".join(text.split()) or seed
    except Exception:
        # fail-safe so search remains functional need this because of shitty gpu
        expanded = seed
        #return seed
    
    #expanded query stored even if idential to seed
    query_cache.set(seed, OLLAMA_MODEL, OLLAMA_TEMP, expanded)

    return expanded
    

