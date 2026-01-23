import axios from "axios";
import { getAuthHeaders, clearCurrentUser } from "../auth/auth.js";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

/**
 * Fetch the current user's settings from the backend.
 * Falls back to defaults if the request fails.
 */
async function getUserSettings() {
    const headers = getAuthHeaders();
    try {
        const res = await axios.get(`${API_BASE}/user/settings`, { headers });
        return res.data;
    } catch (err) {
        console.warn("Failed to fetch user settings, using defaults", err);
        return { use_enhanced_query: true, verbosity: "medium" };
    }
}

/**
 * Perform a search query using the user's current settings.
 *
 * @param {string} query - The raw user query
 */
export async function searchQuery(query) {
    const settings = await getUserSettings();

    const url =
        `${API_BASE}/search` +
        `?q=${encodeURIComponent(query)}` +
        `&use_enhanced=${settings.use_enhanced_query}` +
        `&verbosity=${encodeURIComponent(settings.verbosity)}`;

    const headers = getAuthHeaders();

    try {
        const res = await axios.get(url, { headers });
        return res.data;
    } catch (err) {
        if (err?.response?.status === 401) {
            // Token expired or invalid — force logout and redirect to login
            clearCurrentUser();
            window.location.href = "/login";
            return Promise.reject(
                new Error("Unauthorized: token expired or invalid")
            );
        }
        throw err;
    }
}

export async function logClick({ user_id, query_id, clicked_url, rank }) {
    const url = `${API_BASE}/interactions`;
    const headers = { "Content-Type": "application/json", ...getAuthHeaders() };
    // If you pass user_id in the body it will be ignored if there's a logged-in user.
    try {
        await axios.post(
            url,
            { user_id, query_id, clicked_url, rank },
            { headers }
        );
    } catch (err) {
        if (err?.response?.status === 401) {
            clearCurrentUser();
            window.location.href = "/login";
            return Promise.reject(
                new Error("Unauthorized: token expired or invalid")
            );
        }
        throw err;
    }
}

export async function logFeedback({
                                      user_id,
                                      query_id,
                                      result_url,
                                      rank,
                                      is_relevant,
                                  }) {
    const url = `${API_BASE}/feedback`;
    const headers = { "Content-Type": "application/json", ...getAuthHeaders() };
    // If you pass user_id in the body it will be ignored if there's a logged-in users.
    try {
        //basically identical to logClick
        await axios.post(
            url,
            { user_id, query_id, result_url, rank, is_relevant },
            { headers }
        );
    } catch (err) {
        if (err?.response?.status === 401) {
            clearCurrentUser();
            window.location.href = "/login";
            return Promise.reject(
                new Error("Unauthorized: token expired or invalid")
            );
        }
        throw err;
    }
}
