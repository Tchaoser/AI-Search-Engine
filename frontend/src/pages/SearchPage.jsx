import React, { useState, useEffect } from "react";
import { searchQuery } from "../api/search.js";
import SearchBar from "../components/SearchBar.jsx";
import SearchResults from "../components/SearchResults.jsx";

export default function SearchPage() {
    const [results, setResults] = useState([]);
    const [queryId, setQueryId] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [useEnhanced, setUseEnhanced] = useState(true);
    const [enhancedQuery, setEnhancedQuery] = useState(null);

    useEffect(() => {
        const saved = localStorage.getItem("useEnhancedQuery");
        if (saved !== null) setUseEnhanced(JSON.parse(saved));
    }, []);

    const handleSearch = async (query) => {
        setSearchTerm(query);
        setLoading(true);
        setError(null);
        setEnhancedQuery(null);

        try {
            const data = await searchQuery(query, useEnhanced);
            setQueryId(data.query_id || null);
            setResults(Array.isArray(data.results) ? data.results : []);
            setEnhancedQuery(data.enhanced_query || null);
        } catch (err) {
            console.error(err);
            setError("Failed to fetch results. Is the backend running?");
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const hasResultsOrMessage =
        1;

    /* -- HERO STATE (no search yet) -- */
    if (!hasResultsOrMessage) {
        return (
            <div className="search-hero">
                <h1 className="hero-title">AI Search</h1>
                <p className="hero-subtitle">Smarter results tailored to you</p>

                <div className="hero-search-wrapper">
                    <SearchBar onSearch={handleSearch} hero />
                </div>

                <p className="no-results-msg">No results yet. Try searching above.</p>
            </div>
        );
    }

    /* -- RESULTS STATE -- */
    return (
        <div className="results-page-container container">
            {/* Left side: search + results */}
            <div className="results-left" style={{ flex: 1 }}>
                <SearchBar onSearch={handleSearch} />

                {enhancedQuery && (
                    <div className="enhanced-box">
                        <strong>{useEnhanced ? "Enhanced Query:" : "Query:"}</strong>{" "}
                        {enhancedQuery}
                    </div>
                )}

                {loading && <p className="text-muted mt-2">Loading results...</p>}
                {error && <p className="text-red mt-2">{error}</p>}

                <SearchResults
                    results={results}
                    query_id={queryId}
                    searchTerm={searchTerm}
                    loading={loading}
                />
            </div>

            {/* Right side: insight panel */}
            <div className="insight-panel">
                <h3>Query Insights</h3>
                <p><strong>Original query:</strong> {searchTerm || "—"}</p>
                <p><strong>Enhanced query:</strong> {enhancedQuery || "—"}</p>
                <p><strong>Semantic expansions:</strong> ...</p>
                <p><strong>History effects:</strong> ...</p>
                <p><strong>Interest model updates:</strong> ...</p>
                <p><strong>Most recent log:</strong> ...</p>
            </div>
        </div>
    );
}
