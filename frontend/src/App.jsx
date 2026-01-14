import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Footer from "./components/Footer.jsx";
import SearchPage from "./pages/SearchPage.jsx";
import UserProfilePage from "./pages/UserProfilePage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";

export default function App() {
    return (
        <Router>
            <div className="app-shell">
                {/* NAVBAR */}
                <Navbar />

                {/* MAIN CONTENT */}
                <main className="app-content">
                    <Routes>
                        <Route path="/" element={<SearchPage />} />
                        <Route path="/profile" element={<UserProfilePage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/register" element={<RegisterPage />} />
                    </Routes>
                </main>

                {/* FOOTER */}
                <footer className="app-footer">
                    <Footer />
                </footer>
            </div>
        </Router>
    );
}
