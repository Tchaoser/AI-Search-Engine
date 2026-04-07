import React, { useState, useEffect } from "react";
import { getBenchmarkResults, submitJudgments } from "../api/benchmark.js";

export default function EvaluationPage() {
    const [evaluatorId, setEvaluatorId] = useState(() => localStorage.getItem("evaluatorId") || "");
    const [started, setStarted] = useState(false);
    const [data, setData] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [judgments, setJudgments] = useState({});
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const startEvaluation = async () => {
        if (!evaluatorId.trim()) return;
        localStorage.setItem("evaluatorId", evaluatorId.trim());
        setLoading(true);
        setError(null);
        try {
            const res = await getBenchmarkResults(evaluatorId.trim());
            setData(res);
            // Jump to the first unjudged result
            const firstPending = res.results.findIndex((r) => !r.judged);
            setCurrentIndex(firstPending >= 0 ? firstPending : 0);
            setStarted(true);
        } catch (err) {
            setError("Failed to load benchmark results. Is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    const currentResult = data?.results?.[currentIndex];

    const toggleRelevance = (rank) => {
        const key = `${currentResult._id}_${rank}`;
        setJudgments((prev) => ({ ...prev, [key]: !prev[key] }));
    };

    const isRelevant = (rank) => {
        return !!judgments[`${currentResult._id}_${rank}`];
    };

    const handleSubmit = async () => {
        if (!currentResult) return;
        setSaving(true);
        const labels = currentResult.results.map((r) => ({
            rank: r.rank,
            relevant: isRelevant(r.rank),
        }));
        try {
            await submitJudgments(currentResult._id, evaluatorId.trim(), labels);
            // Mark as judged locally
            setData((prev) => {
                const updated = { ...prev };
                updated.results = [...prev.results];
                updated.results[currentIndex] = { ...updated.results[currentIndex], judged: true };
                updated.judged = (updated.judged || 0) + 1;
                updated.pending = Math.max(0, (updated.pending || 0) - 1);
                return updated;
            });
            // Move to next unjudged
            const nextPending = data.results.findIndex((r, i) => i > currentIndex && !r.judged);
            if (nextPending >= 0) {
                setCurrentIndex(nextPending);
            } else if (currentIndex < data.results.length - 1) {
                setCurrentIndex(currentIndex + 1);
            }
        } catch (err) {
            setError("Failed to save judgment.");
        } finally {
            setSaving(false);
        }
    };

    /* --- Evaluator ID entry screen --- */
    if (!started) {
        return (
            <div className="eval-page">
                <div className="eval-card">
                    <h1 className="eval-title">Benchmark Evaluation</h1>
                    <p className="eval-subtitle">Enter your evaluator ID to begin labeling results.</p>
                    <div className="eval-id-form">
                        <input
                            className="eval-input"
                            type="text"
                            placeholder="Evaluator ID"
                            value={evaluatorId}
                            onChange={(e) => setEvaluatorId(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && startEvaluation()}
                        />
                        <button className="eval-btn eval-btn-primary" onClick={startEvaluation} disabled={loading}>
                            {loading ? "Loading…" : "Start Evaluation"}
                        </button>
                    </div>
                    {error && <p className="eval-error">{error}</p>}
                </div>
            </div>
        );
    }

    /* --- No results --- */
    if (!data?.results?.length) {
        return (
            <div className="eval-page">
                <div className="eval-card">
                    <h2>No benchmark results found.</h2>
                    <p>Run the benchmark script first to generate results.</p>
                </div>
            </div>
        );
    }

    /* --- Main evaluation UI --- */
    const progress = data ? `${data.judged || 0} / ${data.total || 0} judged` : "";

    return (
        <div className="eval-page">
            <div className="eval-card">
                <div className="eval-header">
                    <h1 className="eval-title">Benchmark Evaluation</h1>
                    <span className="eval-progress">{progress}</span>
                </div>

                {/* Navigation */}
                <div className="eval-nav">
                    <button
                        className="eval-btn"
                        disabled={currentIndex === 0}
                        onClick={() => setCurrentIndex(currentIndex - 1)}
                    >
                        ← Previous
                    </button>
                    <span className="eval-nav-label">
                        {currentIndex + 1} of {data.results.length}
                        {currentResult?.judged && <span className="eval-badge-done"> ✓ Judged</span>}
                    </span>
                    <button
                        className="eval-btn"
                        disabled={currentIndex >= data.results.length - 1}
                        onClick={() => setCurrentIndex(currentIndex + 1)}
                    >
                        Next →
                    </button>
                </div>

                {/* Query info */}
                {currentResult && (
                    <div className="eval-query-info">
                        <div><strong>Query ID:</strong> {currentResult.query_id}</div>
                        <div><strong>Experiment Arm:</strong> {currentResult.experiment_arm}</div>
                    </div>
                )}

                {/* Results to judge */}
                {currentResult?.results?.map((r) => (
                    <div
                        key={r.rank}
                        className={`eval-result ${isRelevant(r.rank) ? "eval-result-relevant" : ""}`}
                    >
                        <div className="eval-result-header">
                            <span className="eval-rank">#{r.rank}</span>
                            <button
                                className={`eval-btn-label ${isRelevant(r.rank) ? "relevant" : "not-relevant"}`}
                                onClick={() => toggleRelevance(r.rank)}
                            >
                                {isRelevant(r.rank) ? "✓ Relevant" : "✗ Not Relevant"}
                            </button>
                        </div>
                        <div className="eval-result-title">{r.title || "(no title)"}</div>
                        <div className="eval-result-url">{r.url}</div>
                        <div className="eval-result-snippet">{r.snippet || "(no snippet)"}</div>
                    </div>
                ))}

                {/* Submit */}
                <div className="eval-actions">
                    <button
                        className="eval-btn eval-btn-primary"
                        onClick={handleSubmit}
                        disabled={saving}
                    >
                        {saving ? "Saving…" : "Submit Judgments"}
                    </button>
                </div>

                {error && <p className="eval-error">{error}</p>}
            </div>
        </div>
    );
}
