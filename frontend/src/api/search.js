import axios from "axios";

export async function searchQuery(query) {
    const url = `${import.meta.env.VITE_API_URL}/search?q=${encodeURIComponent(query)}`;
    const res = await axios.get(url);
    return res.data.results || [];
}
