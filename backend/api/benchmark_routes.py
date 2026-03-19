from fastapi import APIRouter, Body, Query
from backend.services.db import benchmark_results_col, relevance_judgments_col
from backend.models.data_models import make_relevance_judgment_doc
from backend.services.logger import AppLogger

router = APIRouter(prefix="/benchmark", tags=["benchmark"])
logger = AppLogger.get_logger(__name__)


@router.get("/results")
async def list_benchmark_results(
    evaluator_id: str = Query(None),
):
    """
    List all benchmark result snapshots.
    If evaluator_id is provided, each result includes whether it has been judged
    by that evaluator, enabling progress tracking.
    """
    results = list(benchmark_results_col.find({}, {"_id": 1, "query_id": 1, "experiment_arm": 1, "results": 1, "timestamp": 1}))

    judged_ids = set()
    if evaluator_id:
        judgments = relevance_judgments_col.find(
            {"evaluator_id": evaluator_id},
            {"benchmark_result_id": 1}
        )
        judged_ids = {j["benchmark_result_id"] for j in judgments}

    for r in results:
        r["judged"] = r["_id"] in judged_ids

    total = len(results)
    judged_count = sum(1 for r in results if r["judged"])

    logger.debug("Benchmark results listed", extra={
        "total": total,
        "judged": judged_count,
        "evaluator_id": evaluator_id,
    })

    return {
        "total": total,
        "judged": judged_count,
        "pending": total - judged_count,
        "results": results,
    }


@router.get("/results/{result_id}")
async def get_benchmark_result(result_id: str):
    """
    Get a single benchmark result by ID, including the query text and top 5 results.
    """
    result = benchmark_results_col.find_one({"_id": result_id})
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Benchmark result not found")
    return result


@router.post("/judgments")
async def submit_judgment(
    benchmark_result_id: str = Body(...),
    evaluator_id: str = Body(...),
    judgments: list = Body(...),
):
    """
    Submit relevance judgments for a benchmark result.

    Body:
      benchmark_result_id: ID of the benchmark result being judged
      evaluator_id: identifier for the evaluator
      judgments: list of {rank: int, relevant: bool}
    """
    # Validate the benchmark result exists
    result = benchmark_results_col.find_one({"_id": benchmark_result_id})
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Benchmark result not found")

    # Replace any existing judgment from this evaluator for this result
    relevance_judgments_col.delete_many({
        "benchmark_result_id": benchmark_result_id,
        "evaluator_id": evaluator_id,
    })

    doc = make_relevance_judgment_doc(benchmark_result_id, evaluator_id, judgments)
    relevance_judgments_col.insert_one(doc)

    logger.info("Relevance judgment submitted", extra={
        "judgment_id": doc["_id"],
        "benchmark_result_id": benchmark_result_id,
        "evaluator_id": evaluator_id,
        "judgment_count": len(judgments),
    })

    return {
        "judgment_id": doc["_id"],
        "status": "saved",
    }


@router.get("/progress")
async def evaluation_progress(evaluator_id: str = Query(...)):
    """
    Get evaluation progress for a specific evaluator.
    Returns counts of total, judged, and pending benchmark results.
    """
    total = benchmark_results_col.count_documents({})
    judged = relevance_judgments_col.count_documents({"evaluator_id": evaluator_id})

    return {
        "evaluator_id": evaluator_id,
        "total": total,
        "judged": judged,
        "pending": max(0, total - judged),
    }
