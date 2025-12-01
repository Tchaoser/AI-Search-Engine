import React, { useState } from "react";
import { saveAuth } from "../auth/auth.js";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [err, setErr] = useState(null);
    const navigate = useNavigate();

    const submit = async (e) => {
        e.preventDefault();
        setErr(null);
        try {
            const res = await fetch(`${API}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Login failed");

            saveAuth({
                access_token: data.access_token,
                user_id: data.user_id
            });

            navigate("/");
        } catch (e) {
            setErr(e.message || "Login failed");
        }
    };

    return (
        <div
            className="profile-card"
            style={{
                maxWidth: "650px",      // bigger login card
                width: "92%",
                margin: "120px auto",   // lower and centered
                padding: "3rem 3rem",   // bigger padding
                borderRadius: "1rem",
            }}
        >
            <h3
                className="profile-section-title"
                style={{ fontSize: "2rem", marginBottom: "2rem" }}
            >
                Login
            </h3>

            {err && (
                <p
                    className="text-red"
                    style={{ fontSize: "1.1rem", marginBottom: "1rem" }}
                >
                    {err}
                </p>
            )}

            <form onSubmit={submit} className="flex flex-col" style={{ gap: "1.5rem" }}>
                <input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="username"
                    className="profile-input"
                    style={{
                        fontSize: "1.2rem",
                        padding: "1rem",
                        height: "55px",
                    }}
                />

                <input
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    type="password"
                    placeholder="password"
                    className="profile-input"
                    style={{
                        fontSize: "1.2rem",
                        padding: "1rem",
                        height: "55px",
                    }}
                />

                <button
                    type="submit"
                    className="profile-save-btn"
                    style={{
                        fontSize: "1.2rem",
                        padding: "0.9rem 1.4rem",
                        width: "150px",
                        marginTop: "0.5rem"
                    }}
                >
                    Login
                </button>
            </form>
        </div>
    );
}
