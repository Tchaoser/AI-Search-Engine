import axios from "axios";

export async function searchQuery(query) {
    const url = `${import.meta.env.VITE_API_URL}/search?q=${encodeURIComponent(query)}`;
    const res = await axios.get(url);
    return res.data;
}

export async function logClick({ user_id, query_id, clicked_url, rank }) {
    const url = `${import.meta.env.VITE_API_URL}/interactions`;
    await axios.post(url, { user_id, query_id, clicked_url, rank });
}
