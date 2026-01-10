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
        <div className="register-page">
            <div className="register-card">
                <h1>Register</h1>

                {msg?.error && (
                    <p className="text-red" style={{ marginBottom: "1rem" }}>
                        {msg.error}
                    </p>
                )}

                {msg?.success && (
                    <p style={{ color: "#15803d", marginBottom: "1rem" }}>
                        {msg.success}
                    </p>
                )}

                <form onSubmit={submit}>

                    {/* Username */}
                    <label htmlFor="username" className="visually-hidden">
                        Username
                    </label>
                    <input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Username"
                        autoComplete="username"
                        required
                    />

                    {/* Email */}
                    <label htmlFor="email" className="visually-hidden">
                        Email address (optional)
                    </label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Email (optional)"
                        autoComplete="email"
                    />

                    {/* Password */}
                    <label htmlFor="password" className="visually-hidden">
                        Password
                    </label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Password"
                        autoComplete="new-password"
                        required
                    />

                    <button type="submit">
                        Register
                    </button>
                </form>
            </div>
        </div>
    );
}
