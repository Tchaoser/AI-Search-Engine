import os, json
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TEMP = float(os.getenv("OLLAMA_TEMP", "0.4"))
ENABLE_SEMANTIC_EXPANSION = os.getenv("ENABLE_SEMANTIC_EXPANSION", "1") in ("1", "true", "True")

SYSTEM_PROMPT = (
    "You expand short user queries into a single, more detailed search query. "
    "Keep it one line, human-readable, and include helpful specifics like entities, "
    "synonyms/aliases in parentheses, constraints (dates/regions/formats), and intent keywords. "
    "Avoid extra commentary—return ONLY the expanded query."
)

async def expand_query(seed: str) -> str:
    """
    Returns a single-line, enhanced query.
    If expansion is disabled or fails, returns the original seed.
    """
    if not ENABLE_SEMANTIC_EXPANSION:
        return seed

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
        # collapse to one line
        return " ".join(text.split()) or seed
    except Exception:
        # Fail-safe: search must remain functional
        return seed