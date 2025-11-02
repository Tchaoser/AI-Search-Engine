import React from "react";
import { Link, useNavigate } from "react-router-dom";
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
                    <Link to="/" className="nav-link">Search</Link>
                    <Link to="/profile" className="nav-link">Profile</Link>
                    <Link to="/settings" className="nav-link">Settings</Link>

                    {userId !== "guest" ? (
                        <button onClick={handleLogout} className="btn btn-link text-sm ml-auto">
                            Logout ({userId})
                        </button>
                    ) : (
                        <>
                            <Link to="/login" className="nav-link ml-auto">Login</Link>
                            <Link to="/register" className="nav-link">Register</Link>
                        </>
                    )}
                </nav>
            </div>
        </header>
    );
}
