import React, { useState, useEffect } from "react";
import { logClick, logFeedback } from "../api/search.js";
import { getCurrentUserId } from "../auth/auth.js";

export default function SearchResults({ results, query_id, searchTerm, loading }) {
    const effectiveUser = getCurrentUserId();
    const [ratings, setRatings] = useState({});

    // Clear ratings when a new query_id comes in (new search)
    useEffect(() => {
        setRatings({});
    }, [query_id]);

    if (!loading && (!results || results.length === 0)) {
        const term = (searchTerm || "").trim();
        return term ? (
            <p className="text-muted">No results found for '{term}'.</p>
        ) : (
            <p className="text-muted">No results yet. Try searching above.</p>
        );
    }

    if (!results || results.length === 0) return null;

    const handleClick = (r, index) => {
        if (!query_id) return;
        logClick({
            user_id: effectiveUser,
            query_id,
            clicked_url: r.link,
            rank: index + 1
        }).catch(err => console.error("Failed to log click:", err));
    };

    const handleRating = (r, index, relevance) => {
        if (!query_id) return;

        const key = r.link || String(index);

        setRatings((prev) => {
            const current = prev[key];
            const next = current === relevance ? null : relevance;
            if (!next) {
                const clone = { ...prev };
                delete clone[key];
                return clone;
            }
            return { ...prev, [key]: next };
        });

        const is_relevant = relevance === "relevant";

        logFeedback({
            user_id: effectiveUser,
            query_id,
            result_url: r.link,
            rank: index + 1,
            is_relevant,
        }).catch((err) => console.error("Failed to log feedback:", err));
    };

    return (
        <div className="results-container">
            {results.map((r, i) => {
                const key = r.link || String(i);
                const rating = ratings[key];

                return (
                    <div key={i} className="result-card">
                        <a
                            href={r.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="result-title"
                            onClick={() => handleClick(r, i)}
                        >
                            {r.title || r.link}
                        </a>

                        {/* Show the URL under the title */}
                        <span className="result-url">{r.link}</span>

                        {r.snippet && (
                            <p className="result-snippet">{r.snippet}</p>
                        )}

                        <div className="result-actions">
                            <button
                                className={
                                    "rate-btn relevant" +
                                    (rating === "relevant" ? " selected" : "")
                                }
                                type="button"
                                onClick={() => handleRating(r, i, "relevant")}
                            >
                                Relevant
                            </button>
                            <button
                                className={
                                    "rate-btn not-relevant" +
                                    (rating === "not_relevant" ? " selected" : "")
                                }
                                type="button"
                                onClick={() => handleRating(r, i, "not_relevant")}
                            >
                                Not Relevant
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
