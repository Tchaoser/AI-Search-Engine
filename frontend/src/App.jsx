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
            <div className="min-h-screen flex flex-col">
                <header className="header bg-blue-100 text-white">
                    <div className="container flex items-center justify-between py-3">
                        <Navbar />
                    </div>
                </header>

                <main className="main container py-6">
                    <Routes>
                        <Route path="/" element={<SearchPage />} />
                        <Route path="/profile" element={<UserProfilePage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/register" element={<RegisterPage />} />
                    </Routes>
                </main>

                <footer className="footer bg-gray-200">
                    <div className="container py-4">
                        <Footer />
                    </div>
                </footer>
            </div>
        </Router>
    );
}
