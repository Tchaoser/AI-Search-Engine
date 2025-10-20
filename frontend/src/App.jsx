import React, { useState } from "react";
import { searchQuery } from "./api/search.js";
import SearchBar from "./components/SearchBar.jsx";
import SearchResults from "./components/SearchResults.jsx";

export default function App() {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = async (query) => {
        setLoading(true);
        setError(null);

        try {
            const data = await searchQuery(query);
            setResults(data);
        } catch (err) {
            console.error(err);
            setError("Failed to fetch results. Is the backend running?");
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-4 max-w-3xl mx-auto">
            <h1 className="text-3xl font-bold text-blue-600 mb-4">AI Search Dev</h1>
            <SearchBar onSearch={handleSearch} />
            {loading && <p className="text-gray-500">Loading results...</p>}
            {error && <p className="text-red-500">{error}</p>}
            <SearchResults results={results} />
        </div>
    );
}
