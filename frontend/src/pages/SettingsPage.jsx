import React, { useState, useEffect } from "react";

export default function SettingsPage() {
    const [useEnhancedQuery, setUseEnhancedQuery] = useState(true);
    const [verbosity, setVerbosity] = useState("medium");
    const [semanticMode, setSemanticMode] = useState("clarify_only");

    // Load from localStorage on mount
    useEffect(() => {
        const savedEnhanced = localStorage.getItem("useEnhancedQuery");
        if (savedEnhanced !== null) {
            setUseEnhancedQuery(JSON.parse(savedEnhanced));
        }

        const savedVerbosity = localStorage.getItem("semanticVerbosity");
        if (savedVerbosity) {
            setVerbosity(savedVerbosity);
        }

        const savedMode = localStorage.getItem("semanticMode");
        if (savedMode) {
            setSemanticMode(savedMode);
        }
    }, []);

    const handleVerbosityChange = (e) => {
        const value = e.target.value;
        setVerbosity(value);
        localStorage.setItem("semanticVerbosity", value);
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
                        <p className="settings-description" id="enhanced-query-desc">
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
                        onClick={() => {
                            const newVal = !useEnhancedQuery;
                            setUseEnhancedQuery(newVal);
                            localStorage.setItem(
                                "useEnhancedQuery",
                                JSON.stringify(newVal)
                            );
                        }}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                const newVal = !useEnhancedQuery;
                                setUseEnhancedQuery(newVal);
                                localStorage.setItem(
                                    "useEnhancedQuery",
                                    JSON.stringify(newVal)
                                );
                            }
                        }}
                    >
                        <div className="settings-switch-knob"></div>
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
                                onChange={handleVerbosityChange}
                                style={{
                                    width: "100%",
                                    padding: "0.5rem",
                                    borderRadius: "0.5rem",
                                    border: "1px solid #cbd5e1",
                                    background: "white",
                                    cursor: "pointer",
                                }}
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
