import React from "react";
import { logClick } from "../api/search.js";
import { getCurrentUserId } from "../auth/auth.js";

export default function SearchResults({ results, query_id, searchTerm, loading }) {
    const effectiveUser = getCurrentUserId();

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
        logClick({
            user_id: effectiveUser,
            query_id,
            clicked_url: r.link,
            rank: index + 1
        }).catch(err => console.error("Failed to log click:", err));
    };

    return (
        <div className="results-container">
            {results.map((r, i) => (
                <div key={i} className="result-card">
                    <div className="result-left">
                        <a
                            href={r.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="result-title"
                            onClick={() => handleClick(r, i)}
                        >
                            {r.title || r.link}
                        </a>

                        {r.snippet && (
                            <p className="result-snippet">{r.snippet}</p>
                        )}
                    </div>

                    <div className="result-actions">
                        <button className="rate-btn relevant">Relevant</button>
                        <button className="rate-btn not-relevant">Not Relevant</button>
                    </div>
                </div>
            ))}
        </div>
    );
}
