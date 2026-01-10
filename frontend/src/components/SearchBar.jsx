import React, { useState, useEffect } from "react";

export default function SearchBar({ onSearch, hero }) {
    const [query, setQuery] = useState("");

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const initialQuery = params.get("query");
        if (initialQuery) setQuery(initialQuery);
    }, []);

    useEffect(() => {
        if (query) {
            window.history.replaceState(
                null,
                "",
                `?query=${encodeURIComponent(query)}`
            );
        }
    }, [query]);

    const handleSubmit = (e) => {
        e.preventDefault();
        const trimmed = query.trim();
        if (trimmed) {
            onSearch(trimmed);
            window.history.replaceState(
                null,
                "",
                `?query=${encodeURIComponent(trimmed)}`
            );
        }
    };

    return (
        <form
            onSubmit={handleSubmit}
            className={`searchbar-wrapper ${hero ? "hero" : ""}`}
            role="search"
        >
            {/* Accessible label */}
            <label htmlFor="search-input" className="visually-hidden">
                Search the site
            </label>

            <div className={`searchbar-container ${hero ? "hero" : ""}`}>
                <span className="searchbar-icon" aria-hidden="true">
                    <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#008C8C"
                        strokeWidth="2.2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <circle cx="11" cy="11" r="7"></circle>
                        <line x1="16.65" y1="16.65" x2="21" y2="21"></line>
                    </svg>
                </span>

                <input
                    id="search-input"
                    type="search"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search anything..."
                    className="searchbar-input-real"
                />
            </div>

            <button type="submit" className="searchbar-btn">
                Search
            </button>
        </form>
    );
}
