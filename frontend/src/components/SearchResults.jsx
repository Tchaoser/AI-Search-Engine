import React from "react";
import { logClick } from "../api/search.js";
import { getCurrentUserId } from "../auth/auth.js";

export default function SearchResults({ results, query_id, user_id }) {
    const effectiveUser = user_id || getCurrentUserId();

    if (!results || results.length === 0) {
        return <p className="text-muted">No results yet. Try searching above.</p>;
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
