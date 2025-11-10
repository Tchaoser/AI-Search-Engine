export function saveAuth({ access_token, user_id }) {
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("user_id", user_id);
}

export function getAccessToken() {
    return localStorage.getItem("access_token");
}

export function getCurrentUserId() {
    return localStorage.getItem("user_id") || "guest";
}

export function clearCurrentUser() {
    localStorage.removeItem("user_id");
    localStorage.removeItem("access_token");
}

export function getAuthHeaders() {
    const token = getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}
