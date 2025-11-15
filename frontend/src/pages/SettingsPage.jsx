import React, { useState, useEffect } from "react";

export default function SettingsPage() {
    const [useEnhancedQuery, setUseEnhancedQuery] = useState(true);

    // Load setting from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem("useEnhancedQuery");
        if (saved !== null) {
            setUseEnhancedQuery(JSON.parse(saved));
        }
    }, []);

    // Save setting to localStorage when it changes
    const handleToggleEnhancedQuery = (e) => {
        const checked = e.target.checked;
        setUseEnhancedQuery(checked);
        localStorage.setItem("useEnhancedQuery", JSON.stringify(checked));
    };

    return (
        <div>
            <h2 className="text-2xl font-semibold mb-3">Settings</h2>
            <p className="text-gray-600">Here users will manage privacy, performance, and personalization options.</p>

            <div className="mt-6 p-4 border border-gray-300 rounded-lg">
                <div className="flex items-center justify-between">
                    <div>
                        <label htmlFor="enhanced-query-toggle" className="text-lg font-medium">
                            Use Enhanced Query
                        </label>
                        <p className="text-sm text-gray-600 mt-1">
                            Enable semantic query expansion to improve search results
                        </p>
                    </div>
                    <input
                        id="enhanced-query-toggle"
                        type="checkbox"
                        checked={useEnhancedQuery}
                        onChange={handleToggleEnhancedQuery}
                        className="w-6 h-6 cursor-pointer"
                    />
                </div>
            </div>
        </div>
    );
}
