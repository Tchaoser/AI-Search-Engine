import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
    return (
        <nav className="bg-blue-600 text-white p-3 mb-4">
            <div className="flex justify-between items-center max-w-3xl mx-auto">
                <h1 className="font-bold text-lg">AI Search Dev</h1>
                <div className="space-x-4">
                    <Link to="/" className="hover:underline">Search</Link>
                    <Link to="/profile" className="hover:underline">Profile</Link>
                    <Link to="/settings" className="hover:underline">Settings</Link>
                </div>
            </div>
        </nav>
    );
}
