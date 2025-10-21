import React from "react";
import { logClick } from "../api/search.js";

export default function SearchResults({ results, query_id, user_id = "guest" }) {
    if (!results || results.length === 0) {
        return <p className="text-gray-500">No results yet. Try searching above.</p>;
    }

    const handleClick = (e, r, index) => {
        logClick({
            user_id,
            query_id,
            clicked_url: r.link,
            rank: index + 1
        }).catch(err => console.error("Failed to log click:", err));
    };

    return (
        <ul className="list-disc pl-5">
            {results.map((r, i) => (
                <li key={i} className="mb-2">
                    <a
                        href={r.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                        onClick={(e) => handleClick(e, r, i)}
                    >
                        {r.title}
                    </a>
                    {r.snippet && <p className="text-gray-700">{r.snippet}</p>}
                </li>
            ))}
        </ul>
    );
}
