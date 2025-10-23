import React, { useState } from "react";
import { searchQuery } from "../api/search.js";
import SearchBar from "../components/SearchBar.jsx";
import SearchResults from "../components/SearchResults.jsx";

export default function SearchPage() {
    const [results, setResults] = useState([]);
    const [queryId, setQueryId] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = async (query) => {
        setLoading(true);
        setError(null);

        try {
            const data = await searchQuery(query);
            setQueryId(data.query_id);
            setResults(data.results);
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
            <SearchBar onSearch={handleSearch} />
            {loading && <p className="text-gray-500 mt-2">Loading results...</p>}
            {error && <p className="text-red-500 mt-2">{error}</p>}
            <SearchResults results={results} query_id={queryId} />
        </div>
    );
}
