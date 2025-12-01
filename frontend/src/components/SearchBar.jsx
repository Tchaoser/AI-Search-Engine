import React, { useState } from "react";

export default function SearchBar({ onSearch, hero }) {
    const [query, setQuery] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();
        const trimmed = query.trim();
        if (trimmed) onSearch(trimmed);
    };

    return (
        <form
            onSubmit={handleSubmit}
            className={`searchbar-wrapper ${hero ? "hero" : ""}`}
            role="search"
        >
            {/* Outer container for the white bar */}
            <div className={`searchbar-container ${hero ? "hero" : ""}`}>
                <span className="searchbar-icon">
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
                    type="search"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search anything..."
                    className="searchbar-input-real"
                />
            </div>

            {/* Search button OUTSIDE the bar */}
            <button type="submit" className="searchbar-btn">
                Search
            </button>
        </form>
    );
}
