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
        <div className="login-page">
            <div className="login-card">
                <h1>Login</h1>

                {err && (
                    <p className="text-red" style={{ marginBottom: "1rem" }}>
                        {err}
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
                        autoComplete="current-password"
                        required
                    />

                    <button type="submit">
                        Login
                    </button>
                </form>
            </div>
        </div>
    );
}
