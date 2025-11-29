import axios from "axios";
import { getAuthHeaders, clearCurrentUser } from "../auth/auth.js";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

export async function searchQuery(query, useEnhanced = true) {
    const url = `${API_BASE}/search?q=${encodeURIComponent(query)}&use_enhanced=${useEnhanced}`;
    const headers = getAuthHeaders();
    try {
        const res = await axios.get(url, { headers });
        return res.data;
    } catch (err) {
        if (err?.response?.status === 401) {
            // Token expired or invalid — force logout and redirect to login
            clearCurrentUser();
            window.location.href = "/login";
            return Promise.reject(new Error("Unauthorized: token expired or invalid"));
        }
        throw err;
    }
}

export async function logClick({ user_id, query_id, clicked_url, rank }) {
    const url = `${API_BASE}/interactions`;
    const headers = { "Content-Type": "application/json", ...getAuthHeaders() };
    // If you pass user_id in the body it will be ignored if there's a logged-in user.
    try {
        await axios.post(url, { user_id, query_id, clicked_url, rank }, { headers });
    } catch (err) {
        if (err?.response?.status === 401) {
            clearCurrentUser();
            window.location.href = "/login";
            return Promise.reject(new Error("Unauthorized: token expired or invalid"));
        }
        throw err;
    }
}
