import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
    return (
        <header className="w-full mb-2">
            <div className="flex flex-col">
                {/* Top row: logo + title */}
                <div className="flex items-center gap-2">
                    {/* TODO: Replace 🔍 with a custom icon */}
                    <span className="text-xl" aria-hidden="true">🔍</span>
                    <span className="text-xl font-semibold">
                        AI Search Dev
                    </span>
                </div>

                {/* Bottom row: nav links */}
                <nav className="flex gap-4">
                    <Link to="/" className="nav-link">Search</Link>
                    <Link to="/profile" className="nav-link">Profile</Link>
                    <Link to="/settings" className="nav-link">Settings</Link>
                </nav>
            </div>
        </header>
    );
}
