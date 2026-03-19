"""
Benchmark scoring script.

Reads stored benchmark results and relevance judgments from MongoDB,
then computes Precision@5 metrics comparing baseline vs expanded arms.

Metrics produced:
  - P@5 per query per arm
  - Average P@5 per arm
  - Win / loss / tie counts (expanded vs baseline)

Usage:
    python -m backend.scripts.score_benchmark
    python -m backend.scripts.score_benchmark --evaluator-id alice
    python -m backend.scripts.score_benchmark --output scores.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from backend.services.db import benchmark_results_col, relevance_judgments_col, queries_col


def fetch_data(evaluator_id: str | None = None):
    """
    Fetch benchmark results and matching relevance judgments from MongoDB.
    If evaluator_id is specified, only that evaluator's judgments are used.
    Returns (results_list, judgments_by_result_id).
    """
    results = list(benchmark_results_col.find({}))

    judgment_filter = {}
    if evaluator_id:
        judgment_filter["evaluator_id"] = evaluator_id
    judgments_raw = list(relevance_judgments_col.find(judgment_filter))

    # Index judgments by benchmark_result_id (keep latest per evaluator)
    judgments_by_result: dict[str, list] = {}
    for j in judgments_raw:
        rid = j["benchmark_result_id"]
        # If multiple evaluators, collect all; if single, latest wins
        if rid not in judgments_by_result:
            judgments_by_result[rid] = j["judgments"]
        else:
            # Later record overwrites (same evaluator) or merge (multi)
            judgments_by_result[rid] = j["judgments"]

    return results, judgments_by_result


def compute_precision_at_k(judgments: list, k: int = 5) -> float:
    """
    Compute P@k from a list of {"rank": int, "relevant": bool} entries.
    Missing ranks are treated as not relevant.
    """
    relevant_count = 0
    for rank in range(1, k + 1):
        entry = next((j for j in judgments if j.get("rank") == rank), None)
        if entry and entry.get("relevant"):
            relevant_count += 1
    return relevant_count / k


def resolve_query_texts(results: list) -> dict[str, str]:
    """
    Map query_id → raw query text by looking up the queries collection.
    """
    query_ids = list({r["query_id"] for r in results})
    if not query_ids:
        return {}
    docs = queries_col.find({"_id": {"$in": query_ids}}, {"_id": 1, "raw_text": 1})
    return {d["_id"]: d["raw_text"] for d in docs}


def score(results: list, judgments_by_result: dict, query_text_map: dict):
    """
    Compute per-query P@5 and aggregate metrics.

    Returns a dict with:
      - per_query: list of {query_text, arm, p_at_5, result_id}
      - summary: {baseline_avg, expanded_avg, baseline_n, expanded_n}
      - comparisons: {wins, losses, ties, details}
      - skipped: count of results without judgments
    """
    # Collect P@5 per result
    per_query = []
    skipped = 0

    for r in results:
        result_id = r["_id"]
        arm = r["experiment_arm"]
        query_id = r["query_id"]
        query_text = query_text_map.get(query_id, query_id)

        if result_id not in judgments_by_result:
            skipped += 1
            continue

        judgments = judgments_by_result[result_id]
        p5 = compute_precision_at_k(judgments, k=5)

        per_query.append({
            "query_text": query_text,
            "query_id": query_id,
            "result_id": result_id,
            "arm": arm,
            "p_at_5": p5,
        })

    # Group by arm for averages
    arm_scores: dict[str, list[float]] = defaultdict(list)
    for entry in per_query:
        arm_scores[entry["arm"]].append(entry["p_at_5"])

    def safe_avg(vals):
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    baseline_scores = arm_scores.get("baseline", [])
    expanded_scores = arm_scores.get("expanded", [])

    summary = {
        "baseline_avg_p5": safe_avg(baseline_scores),
        "expanded_avg_p5": safe_avg(expanded_scores),
        "baseline_n": len(baseline_scores),
        "expanded_n": len(expanded_scores),
    }

    # Win/loss/tie: group per_query by query_text, compare arms
    by_query_text: dict[str, dict[str, float]] = defaultdict(dict)
    for entry in per_query:
        by_query_text[entry["query_text"]][entry["arm"]] = entry["p_at_5"]

    wins = 0    # expanded > baseline
    losses = 0  # expanded < baseline
    ties = 0    # expanded == baseline
    comparison_details = []

    for qt, arms in sorted(by_query_text.items()):
        if "baseline" not in arms or "expanded" not in arms:
            continue  # need both arms to compare
        b = arms["baseline"]
        e = arms["expanded"]
        if e > b:
            outcome = "win"
            wins += 1
        elif e < b:
            outcome = "loss"
            losses += 1
        else:
            outcome = "tie"
            ties += 1
        comparison_details.append({
            "query": qt,
            "baseline_p5": b,
            "expanded_p5": e,
            "outcome": outcome,
        })

    comparisons = {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "compared": wins + losses + ties,
        "details": comparison_details,
    }

    return {
        "per_query": per_query,
        "summary": summary,
        "comparisons": comparisons,
        "skipped": skipped,
    }


def print_report(report: dict):
    """Print a human-readable summary to stdout."""
    summary = report["summary"]
    comp = report["comparisons"]
    skipped = report["skipped"]

    print("=" * 60)
    print("  BENCHMARK SCORING REPORT")
    print("=" * 60)
    print()

    print(f"  Results judged:   {summary['baseline_n'] + summary['expanded_n']}")
    print(f"  Results skipped:  {skipped} (no judgments)")
    print()

    print("  Average Precision@5")
    print(f"    Baseline:  {summary['baseline_avg_p5']:.4f}  (n={summary['baseline_n']})")
    print(f"    Expanded:  {summary['expanded_avg_p5']:.4f}  (n={summary['expanded_n']})")
    diff = summary["expanded_avg_p5"] - summary["baseline_avg_p5"]
    sign = "+" if diff >= 0 else ""
    print(f"    Delta:     {sign}{diff:.4f}")
    print()

    if comp["compared"] > 0:
        print(f"  Head-to-Head (expanded vs baseline, n={comp['compared']})")
        print(f"    Wins:   {comp['wins']}")
        print(f"    Losses: {comp['losses']}")
        print(f"    Ties:   {comp['ties']}")
        print()

        print("  Per-Query Comparisons:")
        print(f"  {'Query':<45} {'Baseline':>8} {'Expanded':>8} {'Result':>7}")
        print("  " + "-" * 70)
        for d in comp["details"]:
            label = d["query"][:44]
            print(f"  {label:<45} {d['baseline_p5']:>8.2f} {d['expanded_p5']:>8.2f} {d['outcome']:>7}")
    else:
        print("  No head-to-head comparisons available.")
        print("  (Need both baseline and expanded judgments for the same query)")

    print()
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Score benchmark results using relevance judgments.")
    parser.add_argument("--evaluator-id", default=None,
                        help="Only use judgments from this evaluator (default: all)")
    parser.add_argument("--output", default=None,
                        help="Write JSON report to this file path")
    args = parser.parse_args()

    results, judgments_by_result = fetch_data(evaluator_id=args.evaluator_id)

    if not results:
        print("No benchmark results found in the database.")
        sys.exit(0)

    query_text_map = resolve_query_texts(results)
    report = score(results, judgments_by_result, query_text_map)

    print_report(report)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"  JSON report saved to {out_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
