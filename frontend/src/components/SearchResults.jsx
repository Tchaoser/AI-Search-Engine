import React from "react";

export default function SearchResults({ results }) {
    if (!results || results.length === 0) {
        return <p className="text-gray-500">No results yet. Try searching above.</p>;
    }

    return (
        <ul className="list-disc pl-5">
            {results.map((r, i) => (
                <li key={i} className="mb-2">
                    <a href={r.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {r.title}
                    </a>
                    {r.snippet && <p className="text-gray-700">{r.snippet}</p>}
                </li>
            ))}
        </ul>
    );
}
