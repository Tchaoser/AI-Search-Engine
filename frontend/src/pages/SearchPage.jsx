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
    const [insight, setInsight] = useState(null);

    useEffect(() => {
        const saved = localStorage.getItem("useEnhancedQuery");
        if (saved !== null) setUseEnhanced(JSON.parse(saved));
    }, []);

    const handleSearch = async (query) => {
        setSearchTerm(query);
        setLoading(true);
        setError(null);
        setInsight(null);

        try {
            const data = await searchQuery(query);
            setQueryId(data.query_id || null);
            setResults(Array.isArray(data.results) ? data.results : []);
            setInsight(data.insight || null);
        } catch (err) {
            console.error(err);
            setError("Failed to fetch results. Is the backend running?");
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const hasResultsOrMessage = searchTerm.trim().length > 0 || loading || error || results.length > 0;

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

                {insight?.expanded_query && (
                    <div className="enhanced-box">
                        <strong>{useEnhanced ? "Enhanced Query:" : "Query:"}</strong>{" "}
                        {insight.expanded_query}
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

                <p className="insight-explanation">
                    Your past searches and clicks help build a profile of your interests.
                    This profile is used to personalize search results and guide semantic expansion.
                </p>

                {insight ? (
                    <>
                        <p><strong>Original Query:</strong> {insight.original_query || "—"}</p>
                        <p><strong>Enhanced Query:</strong> {insight.expanded_query || "—"}</p>
                        <p><strong>Semantic Mode:</strong> {insight.semantic_mode}</p>
                        <p><strong>Verbosity:</strong> {insight.verbosity}</p>

                        {insight.top_explicit?.length > 0 && (
                            <p><strong>Top Explicit Interests Used:</strong> {insight.top_explicit.join(", ")}</p>
                        )}
                        {insight.top_implicit?.length > 0 && (
                            <p><strong>Top Implicit Interests Used:</strong> {insight.top_implicit.join(", ")}</p>
                        )}

                        <p><strong>Cache Status:</strong> {insight.cache_status}</p>
                        <p><strong>Queries Considered:</strong> {insight.queries_considered || "—"}</p>
                        <p><strong>Clicks Considered:</strong> {insight.interactions_considered || "—"}</p>

                    </>
                ) : (
                    <p>No insights available yet.</p>
                )}
            </div>


        </div>
    );
}
