import React, { useState, useEffect } from "react";

export default function SettingsPage() {
    const [useEnhancedQuery, setUseEnhancedQuery] = useState(true);

    // Load from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem("useEnhancedQuery");
        if (saved !== null) {
            setUseEnhancedQuery(JSON.parse(saved));
        }
    }, []);

    return (
        <div className="container settings-page">

            {/* Accessibility label */}
            <h1 className="settings-title">Settings</h1>

            <p className="settings-subtext">
                Here users will manage privacy, performance, and personalization options.
            </p>

            {/* SETTINGS CARD */}
            <div className="settings-card">

                <div className="settings-row">
                    <div className="settings-left">

                        {}
                        <label
                            className="settings-label"
                            id="enhanced-query-label"
                        >
                            Use Enhanced Query
                        </label>

                        <p
                            className="settings-description"
                            id="enhanced-query-desc"
                        >
                            Enable semantic query enhancement to improve search results
                        </p>
                    </div>

                    {/* TOGGLE */}
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

            </div>

        </div>
    );
}
