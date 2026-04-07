"""
Benchmark runner script.

Executes every query from benchmark_queries.json twice against the search API:
  1. Baseline  — use_enhanced=false
  2. Expanded  — use_enhanced=true, semantic_mode=clarify_only

Both runs use benchmark_mode=true so personalization / reranking are disabled
and results are snapshotted automatically by the API.

Usage:
    python -m backend.scripts.run_benchmark                        # default: http://localhost:8000
    python -m backend.scripts.run_benchmark --base-url http://host:port
    python -m backend.scripts.run_benchmark --output results.json  # custom output path
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

QUERIES_PATH = Path(__file__).parent / "benchmark_queries.json"

BASELINE_PARAMS = {
    "use_enhanced": "false",
    "benchmark_mode": "true",
}

EXPANDED_PARAMS = {
    "use_enhanced": "true",
    "semantic_mode": "clarify_only",
    "benchmark_mode": "true",
}

ARMS = [
    ("baseline", BASELINE_PARAMS),
    ("expanded", EXPANDED_PARAMS),
]


def load_queries(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["queries"]


def run_query(base_url: str, query_text: str, params: dict) -> dict:
    """Call the /search endpoint and return the JSON response."""
    qs = urlencode({"q": query_text, **params})
    url = f"{base_url}/search?{qs}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def run_benchmark(base_url: str, queries: list[dict]) -> list[dict]:
    """Run every query in both arms and collect results."""
    records: list[dict] = []
    total = len(queries) * len(ARMS)
    completed = 0

    for entry in queries:
        qid = entry["id"]
        query_text = entry["query"]
        query_type = entry["type"]

        for arm_name, arm_params in ARMS:
            completed += 1
            print(f"[{completed}/{total}] query {qid} ({query_type}) — {arm_name}")

            try:
                start = time.time()
                data = run_query(base_url, query_text, arm_params)
                elapsed_ms = round((time.time() - start) * 1000, 2)

                records.append({
                    "benchmark_query_id": qid,
                    "query_text": query_text,
                    "query_type": query_type,
                    "experiment_arm": arm_name,
                    "api_query_id": data.get("query_id"),
                    "original_query": data.get("original_query"),
                    "enhanced_query": data.get("enhanced_query"),
                    "use_enhanced": data.get("use_enhanced"),
                    "semantic_mode": data.get("semantic_mode"),
                    "benchmark_mode": data.get("benchmark_mode"),
                    "result_count": len(data.get("results", [])),
                    "top5": [
                        {
                            "rank": i + 1,
                            "title": r.get("title", ""),
                            "url": r.get("link", ""),
                            "snippet": r.get("snippet", ""),
                        }
                        for i, r in enumerate(data.get("results", [])[:5])
                    ],
                    "elapsed_ms": elapsed_ms,
                })
            except Exception as exc:
                print(f"  ERROR: {exc}", file=sys.stderr)
                records.append({
                    "benchmark_query_id": qid,
                    "query_text": query_text,
                    "query_type": query_type,
                    "experiment_arm": arm_name,
                    "error": str(exc),
                })

    return records


def main():
    parser = argparse.ArgumentParser(description="Run benchmark experiment against the search API.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("BENCHMARK_API_URL", "http://localhost:8000"),
        help="Base URL of the running search API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write the results JSON (default: backend/scripts/benchmark_results_<timestamp>.json)",
    )
    args = parser.parse_args()

    queries = load_queries(QUERIES_PATH)
    print(f"Loaded {len(queries)} benchmark queries from {QUERIES_PATH.name}")
    print(f"Target API: {args.base_url}")
    print(f"Arms: {', '.join(name for name, _ in ARMS)}")
    print()

    records = run_benchmark(args.base_url, queries)

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = Path(__file__).parent / f"benchmark_results_{ts}.json"

    # Build output document
    output = {
        "experiment_timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "total_queries": len(queries),
        "total_runs": len(records),
        "errors": sum(1 for r in records if "error" in r),
        "records": records,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"Benchmark complete: {len(records)} runs ({output['errors']} errors)")
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
