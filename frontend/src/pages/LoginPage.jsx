import React, { useState } from "react";
import { saveAuth } from "../auth/auth.js";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [err, setErr] = useState(null);
    const navigate = useNavigate(); // <-- add navigation

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

            // Save the auth info
            saveAuth({ access_token: data.access_token, user_id: data.user_id });

            // Redirect to home page
            navigate("/");

            // Force update any user-dependent components if needed
        } catch (e) {
            setErr(e.message || "Login failed");
        }
    };

    return (
        <div className="card">
            <h3>Login</h3>
            {err && <p className="text-red">{err}</p>}
            <form onSubmit={submit} className="flex flex-col gap-2">
                <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" className="input"/>
                <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="password" className="input"/>
                <div className="flex gap-2">
                    <button className="btn btn-primary" type="submit">Login</button>
                </div>
            </form>
        </div>
    );
}
