import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
    const [results, setResults] = useState([])

    useEffect(() => {
        console.log("API URL is:", import.meta.env.VITE_API_URL)
        const url = `${import.meta.env.VITE_API_URL}/search?q=test`
        axios.get(url)
            .then(res => setResults(res.data.results || []))
            .catch(() => setResults([{ id: 0, title: "Backend not running" }]))
    }, [])

    return (
        <div className="p-4">
            <h1 className="text-3xl font-bold text-blue-600 mb-4">AI Search Dev</h1>
            <p className="mb-2 text-gray-700">Frontend is working ✅</p>
            <ul className="list-disc pl-5">
                {results.map(r => <li key={r.id}>{r.title}</li>)}
            </ul>
        </div>
    )
}

export default App
