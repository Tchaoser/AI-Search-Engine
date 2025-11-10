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
        if (!res.ok) setMsg({ error: data.detail || "Register failed" });
        else setMsg({ success: `Registered ${data.user_id}. You can now log in.` });
    };

    return (
        <div className="card">
            <h3>Register</h3>
            {msg?.error && <p className="text-red">{msg.error}</p>}
            {msg?.success && <p className="text-green">{msg.success}</p>}
            <form onSubmit={submit} className="flex flex-col gap-2">
                <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" className="input"/>
                <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email (optional)" className="input"/>
                <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="password" className="input"/>
                <div className="flex gap-2">
                    <button className="btn btn-primary" type="submit">Register</button>
                </div>
            </form>
        </div>
    );
}
