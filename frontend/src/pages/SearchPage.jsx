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

    // Load the useEnhancedQuery setting from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem("useEnhancedQuery");
        if (saved !== null) {
            setUseEnhanced(JSON.parse(saved));
        }
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

    return (
        <div>
            <h2 className="text-2xl font-semibold mb-3 text-left">Search</h2>
            <p className="text-subtle mb-4 text-left">
                Enter a query to retrieve results. Click a result to log interactions.
            </p>

            {enhancedQuery && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    {useEnhanced ? (
                        <p className="text-sm text-gray-600"><strong>Enhanced Query:</strong> {enhancedQuery}</p>
                    ) : (
                        <p className="text-sm text-gray-600"><strong>Query:</strong> {enhancedQuery} (enhancement disabled)</p>
                    )}
                </div>
            )}

            <SearchBar onSearch={handleSearch} />
            {loading && <p className="text-muted mt-2">Loading results...</p>}
            {error && <p className="text-red mt-2">{error}</p>}

            <div className="mt-1">
                <SearchResults results={results} query_id={queryId} searchTerm={searchTerm} loading={loading} />
            </div>
        </div>
    );
}
