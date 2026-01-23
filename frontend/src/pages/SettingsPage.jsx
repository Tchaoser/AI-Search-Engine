// src/pages/SettingsPage.jsx
import React, { useState, useEffect, useCallback } from "react";
import { getCurrentUserId } from "../auth/auth.js";

const API_URL = "http://localhost:5000";

export default function SettingsPage() {
    const [userId] = useState(getCurrentUserId());

    const [useEnhancedQuery, setUseEnhancedQuery] = useState(true);
    const [verbosity, setVerbosity] = useState("medium");
    const [loading, setLoading] = useState(false);
    const [semanticMode, setSemanticMode] = useState("clarify_only");

    //  LOAD SETTINGS 
    const loadSettings = useCallback(() => {
        fetch(`${API_URL}/user/settings?user_id=${userId}`)
            .then(res => res.ok ? res.json() : Promise.reject())
            .then(settings => {
                setUseEnhancedQuery(settings.use_enhanced_query ?? true);
                setVerbosity(settings.verbosity ?? "medium");
            })
            .catch(() => {
                console.warn("Could not load settings, using defaults");
            });
    }, [userId]);
    useEffect(() => {
        loadSettings();
    }, [loadSettings]);

    //  UPDATE SETTINGS 
    const updateSettings = (partial) => {
        setLoading(true);

        fetch(`${API_URL}/user/settings?user_id=${userId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(partial),
        })
            .then(() => loadSettings())
            .finally(() => setLoading(false));
    };

    const toggleEnhancedQuery = () => {
        updateSettings({ use_enhanced_query: !useEnhancedQuery });
    };

    const handleVerbosityChange = (e) => {
        updateSettings({ verbosity: e.target.value });
    };

    const handleSemanticModeChange = (e) => {
        const value = e.target.value;
        setSemanticMode(value);
        localStorage.setItem("semanticMode", value);
    };

    return (
        <div className="container settings-page">
            <h1 className="settings-title">Settings</h1>

            <p className="settings-subtext">
                Manage privacy, performance, and personalization options.
            </p>

            <div className="settings-card">
                {/* Semantic Expansion Toggle */}
                <div className="settings-row">
                    <div className="settings-left">
                        <label className="settings-label" id="enhanced-query-label">
                            <strong>Use Enhanced Query</strong>
                        </label>
                        <p
                            className="settings-description"
                            id="enhanced-query-desc"
                        >
                            Enable semantic query expansion to improve search results
                        </p>
                    </div>

                    <div
                        className={`settings-switch ${useEnhancedQuery ? "on" : ""}`}
                        role="switch"
                        aria-checked={useEnhancedQuery}
                        aria-labelledby="enhanced-query-label"
                        aria-describedby="enhanced-query-desc"
                        tabIndex={0}
                        onClick={toggleEnhancedQuery}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                toggleEnhancedQuery();
                            }
                        }}
                    >
                        <div className="settings-switch-knob" />
                    </div>
                </div>

                {/* Verbosity Selector */}
                {useEnhancedQuery && (
                    <div className="settings-row" style={{ marginTop: "1.5rem" }}>
                        <div className="settings-left">
                            <label className="settings-label" htmlFor="verbosity-select">
                                <strong>Personalization Verbosity</strong>
                            </label>
                            <p className="settings-description">
                                Controls how many of your interests influence semantic expansion
                            </p>
                        </div>

                        <div className="dropdown" style={{ width: "200px" }}>
                            <select
                                id="verbosity-select"
                                className="settings-select"
                                value={verbosity}
                                disabled={loading}
                                onChange={handleVerbosityChange}
                            >
                                <option value="off">Off</option>
                                <option value="low">Low (strong interests only)</option>
                                <option value="medium">Medium (strong + medium)</option>
                                <option value="high">High (all interests)</option>
                            </select>
                        </div>
                    </div>
                )}
                {/* Semantic Mode Selector */}
                {useEnhancedQuery && (
                    <div className="settings-row" style={{ marginTop: "1.5rem" }}>
                        <div className="settings-left">
                            <label className="settings-label" htmlFor="semantic-mode-select">
                                <strong>Query Interpretation Mode</strong>
                            </label>
                            <p className="settings-description">
                                Determines whether strong interests may resolve ambiguous queries
                            </p>
                        </div>

                        <div className="dropdown" style={{ width: "320px" }}>
                            <select
                                id="semantic-mode-select"
                                className="settings-select"
                                value={semanticMode}
                                onChange={handleSemanticModeChange}
                                style={{
                                    width: "100%",
                                    padding: "0.5rem",
                                    borderRadius: "0.5rem",
                                    border: "1px solid #cbd5e1",
                                    background: "white",
                                    cursor: "pointer",
                                }}
                            >
                                <option value="clarify_only">
                                    Conservative (only clarify intent using interests)
                                </option>
                                <option value="clarify_and_personalize">
                                    Personalized (use strong interests to resolve ambiguity)
                                </option>
                            </select>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
