import axios from "axios";
import { getAuthHeaders } from "../auth/auth.js";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

export async function searchQuery(query) {
    const url = `${API_BASE}/search?q=${encodeURIComponent(query)}`;
    const headers = getAuthHeaders();
    const res = await axios.get(url, { headers });
    return res.data;
}

export async function logClick({ user_id, query_id, clicked_url, rank }) {
    const url = `${API_BASE}/interactions`;
    const headers = { "Content-Type": "application/json", ...getAuthHeaders() };
    // If you pass user_id in the body it will be ignored if there's a logged-in user.
    await axios.post(url, { user_id, query_id, clicked_url, rank }, { headers });
}
