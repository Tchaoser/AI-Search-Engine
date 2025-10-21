import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import SearchPage from "./pages/SearchPage.jsx";
import UserProfilePage from "./pages/UserProfilePage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";

export default function App() {
    return (
        <Router>
            <div className="min-h-screen bg-gray-50 text-gray-900">
                <Navbar />
                <div className="p-4 max-w-3xl mx-auto">
                    <Routes>
                        <Route path="/" element={<SearchPage />} />
                        <Route path="/profile" element={<UserProfilePage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                    </Routes>
                </div>
            </div>
        </Router>
    );
}
