import React from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import { clearCurrentUser, getCurrentUserId } from "../auth/auth.js";

export default function Navbar() {
    const navigate = useNavigate();
    const userId = getCurrentUserId();

    const handleLogout = () => {
        clearCurrentUser();
        navigate("/");  // redirect to search/home page. This also refreshes to update any user-dependent state
    };

    return (
        <header className="w-full mb-2">
            <div className="flex flex-col">
                <div className="flex items-center gap-2">
                    <span className="text-xl" aria-hidden="true">🔍</span> {/* TODO: Replace 🔍 with a custom icon */}
                    <span className="text-xl font-semibold">AI Search Dev</span>
                </div>

                <nav className="flex gap-4 items-center">
                    <NavLink to="/" end className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Search</NavLink>
                    <NavLink to="/profile" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Profile</NavLink>
                    <NavLink to="/settings" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Settings</NavLink>

                    {userId !== "guest" ? (
                        <button onClick={handleLogout} className="btn btn-link text-sm ml-auto">
                            Logout ({userId})
                        </button>
                    ) : (
                        <div className="ml-auto flex gap-2">
                            <NavLink to="/login" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Login</NavLink>
                            <NavLink to="/register" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Register</NavLink>
                        </div>
                    )}
                </nav>
            </div>
        </header>
    );
}
