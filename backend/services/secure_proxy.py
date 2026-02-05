# secure_proxy.py
#
# This service acts as a secure middle-man between the application backend
# and the Google Custom Search API.
# It is designed to:
# - Enforce TLS certificate validation
# - Optionally apply certificate pinning
# - Sanitize external API responses
# - Prevent the main application from directly contacting Google

import os
import ssl
import socket
import hashlib
import logging
from fastapi import FastAPI, HTTPException, Query
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("secure_proxy")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

if not GOOGLE_API_KEY or not GOOGLE_CX:
    logger.critical("Missing required Google API credentials")
    raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_CX in environment variables")

# --- Optional: Certificate pinning toggle ---
# When enabled, the proxy verifies that Google's certificate matches
# a known-good fingerprint.

ENABLE_PINNING = os.getenv("ENABLE_PINNING", "False").lower() == "true"

# Stores Google's certificate fingerprint in memory after the first fetch.
# This makes it so that we do not need to perform a costly TLS handshake on every request while

CACHED_GOOGLE_FINGERPRINT = None

app = FastAPI(title="Secure Google Proxy")


# --- Helper: Fetch & cache Google certificate fingerprint ---
# Establishes a direct TLS connection to Google and extracts the
# SHA-256 fingerprint of the server certificate.

def get_google_cert_fingerprint(hostname="www.googleapis.com", port=443):
    global CACHED_GOOGLE_FINGERPRINT

    if CACHED_GOOGLE_FINGERPRINT:
        return CACHED_GOOGLE_FINGERPRINT

    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_bin = ssock.getpeercert(True)
                fingerprint = hashlib.sha256(cert_bin).hexdigest()
                CACHED_GOOGLE_FINGERPRINT = fingerprint
                logger.info("Cached Google certificate fingerprint")
                return fingerprint
    except Exception as e:
        logger.error(f"Failed to fetch Google certificate fingerprint: {e}")
        return None


# --- Warm-up on startup  ---
# Pre-fetch the certificate fingerprint at service startup when
# certificate pinning is enabled.
# This makes the first request faster

@app.on_event("startup")
def warm_up_cert():
    if ENABLE_PINNING:
        logger.info("Certificate pinning enabled — warming up fingerprint")
        get_google_cert_fingerprint()


# --- Certificate Verification & Pinning ---
# Performs the outbound request to Google with:
# - Default TLS validation
# - Optional certificate pinning
# - Response sanitization

def fetch_google(url: str, params: dict):
    try:
        resp = requests.get(
            url,
            params=params,
            timeout=10,
            verify=True,
            stream=True
        )

        if ENABLE_PINNING:
            pinned_fp = get_google_cert_fingerprint()
            if not pinned_fp:
                raise HTTPException(status_code=502, detail="Certificate fingerprint unavailable")

            cert_bin = resp.raw.connection.sock.getpeercert(True)
            runtime_fp = hashlib.sha256(cert_bin).hexdigest()

            if runtime_fp.lower() != pinned_fp.lower():
                logger.error("Certificate pinning mismatch detected")
                raise HTTPException(status_code=502, detail="Certificate pinning failure")

        resp.raise_for_status()
        data = resp.json()

        # --- Basic response sanitization ---
        return [
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
            }
            for item in data.get("items", [])
        ]

    except requests.exceptions.RequestException as e:
        logger.error(f"Google API request failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch from Google")


# --- Proxy Endpoint ---
# The backend must call this endpoint instead of contacting Google
# directly, ensuring all traffic passes through the security layer.

@app.get("/search")
def secure_search(
    q: str = Query(..., min_length=1),
    num: int = Query(10, gt=0, le=10)
):
    logger.info(f"Received search request: query='{q}' num={num}")

    google_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": q,
        "num": num,
    }

    results = fetch_google(google_url, params)
    logger.info(f"Returning {len(results)} sanitized results")
    return {"items": results}
