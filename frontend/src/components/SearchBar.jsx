import React, { useState } from "react";

export default function SearchBar({ onSearch }) {
    const [query, setQuery] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();
        const trimmed = query.trim();
        if (trimmed) onSearch(trimmed);
    };

    return (
        <form onSubmit={handleSubmit} className="flex flex-col gap-2" role="search">
            <label htmlFor="search-input" className="sr-only">Search</label>
            <input
                id="search-input"
                type="search"
                autoComplete="off"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query..."
                className="input flex-1"
                aria-label="Search query"
            />
            <button
                type="submit"
                className="btn btn-primary btn-focus w-full"
            >
                Search
            </button>
        </form>
    );
}
