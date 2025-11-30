import React, { useState, useRef, useEffect } from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import { clearCurrentUser, getCurrentUserId } from "../auth/auth.js";

export default function Navbar() {
    const navigate = useNavigate();
    const userId = getCurrentUserId();

    const [open, setOpen] = useState(false);
    const dropdownRef = useRef(null);

    const handleLogout = () => {
        clearCurrentUser();
        navigate("/");
    };

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <header className="navbar">
            <div className="navbar-inner">

                <Link to="/" className="navbar-logo">AI Search</Link>

                <nav className="navbar-links">
                    <NavLink to="/" end className="nav-item">Home</NavLink>
                    <NavLink to="/profile" className="nav-item">Profile</NavLink>
                    <NavLink to="/settings" className="nav-item">Settings</NavLink>
                </nav>

                <div className="navbar-auth" ref={dropdownRef}>
                    {userId !== "guest" ? (
                        <button onClick={handleLogout} className="signout-btn">
                            Logout ({userId})
                        </button>
                    ) : (
                        <div className="dropdown">

                            <button
                                className="dropdown-toggle"
                                onClick={() => setOpen((prev) => !prev)}
                            >
                                Sign-In ▾
                            </button>

                            {open && (
                                <div className="dropdown-menu">
                                    <Link to="/login" onClick={() => setOpen(false)}>Login</Link>
                                    <Link to="/register" onClick={() => setOpen(false)}>Register</Link>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
