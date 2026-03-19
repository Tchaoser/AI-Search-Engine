import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

/**
 * Fetch all benchmark results with optional evaluator progress.
 */
export async function getBenchmarkResults(evaluatorId) {
    const params = evaluatorId ? `?evaluator_id=${encodeURIComponent(evaluatorId)}` : "";
    const res = await axios.get(`${API_BASE}/benchmark/results${params}`);
    return res.data;
}

/**
 * Fetch a single benchmark result by ID.
 */
export async function getBenchmarkResult(resultId) {
    const res = await axios.get(`${API_BASE}/benchmark/results/${resultId}`);
    return res.data;
}

/**
 * Submit relevance judgments for a benchmark result.
 */
export async function submitJudgments(benchmarkResultId, evaluatorId, judgments) {
    const res = await axios.post(`${API_BASE}/benchmark/judgments`, {
        benchmark_result_id: benchmarkResultId,
        evaluator_id: evaluatorId,
        judgments,
    });
    return res.data;
}

/**
 * Get evaluation progress for an evaluator.
 */
export async function getEvaluationProgress(evaluatorId) {
    const res = await axios.get(`${API_BASE}/benchmark/progress?evaluator_id=${encodeURIComponent(evaluatorId)}`);
    return res.data;
}
