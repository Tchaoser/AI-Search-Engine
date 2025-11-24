import React from "react";
import { logClick } from "../api/search.js";
import { getCurrentUserId } from "../auth/auth.js";

export default function SearchResults({ results, query_id, user_id, searchTerm, loading }) {
    const effectiveUser = user_id || getCurrentUserId();

    // Only show no-results message when loading is finished and there are no results
    if (!loading && (!results || results.length === 0)) {
        const term = (searchTerm || "").trim();
        if (term) {
            return <p className="text-muted">No results found for '{term}'. Try a different keyword or check your spelling.</p>;
        }
        return <p className="text-muted">No results yet. Try searching above.</p>;
    }

    // Don't show anything while loading or if there are results
    if (!results || results.length === 0) {
        return null;
    }

    const handleClick = (r, index) => {
        logClick({
            user_id: effectiveUser,
            query_id,
            clicked_url: r.link,
            rank: index + 1
        }).catch(err => console.error("Failed to log click:", err));
    };

    return (
        <div className="flex flex-col gap-2">
            {results.map((r, i) => (
                <div
                    key={i}
                    className={`card-compact${i === 0 ? " mt-2" : ""}`}
                >
                    <a
                        href={r.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue font-medium text-base text-blue-hover"
                        onClick={() => handleClick(r, i)}
                    >
                        {r.title || r.link}
                    </a>
                    {r.snippet && <p className="text-subtle mt-1">{r.snippet}</p>}
                </div>
            ))}
        </div>
    );
}
