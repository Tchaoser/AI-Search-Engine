import React, { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function RegisterPage() {
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [msg, setMsg] = useState(null);

    const submit = async (e) => {
        e.preventDefault();
        setMsg(null);

        const res = await fetch(`${API}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            setMsg({ error: data.detail || "Register failed" });
        } else {
            setMsg({ success: `Registered ${data.user_id}. You can now log in.` });
        }
    };

    return (
        <div
            className="profile-card"
            style={{
                maxWidth: "650px",
                width: "92%",
                margin: "120px auto",
                padding: "3rem 3rem",
                borderRadius: "1rem",
            }}
        >
            <h3
                className="profile-section-title"
                style={{ fontSize: "2rem", marginBottom: "2rem" }}
            >
                Register
            </h3>

            {msg?.error && (
                <p className="text-red" style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
                    {msg.error}
                </p>
            )}

            {msg?.success && (
                <p
                    className="text-green"
                    style={{ fontSize: "1.1rem", marginBottom: "1rem", color: "#15803d" }}
                >
                    {msg.success}
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
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="email (optional)"
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
                    className="profile-save-btn"
                    type="submit"
                    style={{
                        fontSize: "1.2rem",
                        padding: "0.9rem 1.4rem",
                        width: "150px",
                        marginTop: "0.5rem",
                    }}
                >
                    Register
                </button>
            </form>
        </div>
    );
}
