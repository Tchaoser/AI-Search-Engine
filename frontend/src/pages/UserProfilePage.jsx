import React, { useState, useEffect } from "react";

export default function UserProfilePage() {
    const [interests, setInterests] = useState(() => {
        try {
            const raw = localStorage.getItem("demo_interests");
            return raw ? JSON.parse(raw) : ["machine learning", "renewable energy", "ui design"];
        } catch {
            return ["machine learning", "renewable energy", "ui design"];
        }
    });
    const [newInterest, setNewInterest] = useState("");

    useEffect(() => {
        try {
            localStorage.setItem("demo_interests", JSON.stringify(interests));
        } catch {}
    }, [interests]);

    const handleAddInterest = () => {
        const trimmed = newInterest.trim().toLowerCase();
        if (!trimmed) return;
        if (!interests.includes(trimmed)) setInterests(prev => [...prev, trimmed]);
        setNewInterest("");
    };

    const handleRemoveInterest = (interest) => {
        setInterests(prev => prev.filter(i => i !== interest));
    };

    return (
        <div>
            <h2 className="text-2xl font-semibold mb-3 text-left">User Profile</h2>
            <p className="text-subtle mb-6 text-left">
                Manage your explicit interests - these are used to personalize results. You can also promote inferred interests later.
            </p>

            <section className="card">
                <h3 className="text-lg font-medium mb-2">Explicit Interests</h3>
                <label htmlFor="interest-input" className="sr-only">Add interest</label>
                <div className="flex flex-col gap-2">
                    <input
                        id="interest-input"
                        type="text"
                        placeholder="Add a new interest (e.g., 'data visualization')"
                        value={newInterest}
                        onChange={(e) => setNewInterest(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddInterest())}
                        className="input flex-1"
                        aria-label="Add new interest"
                    />
                    <button
                        onClick={handleAddInterest}
                        className="btn btn-primary btn-focus"
                        aria-label="Add interest"
                    >
                        Add
                    </button>
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                    {interests.length === 0 && <p className="text-muted italic">No interests yet.</p>}
                    {interests.map((interest) => (
                        <div
                            key={interest}
                            className="inline-flex items-center gap-2 py-1"
                        >
                            <span className="text-sm">{interest}</span>
                            <button
                                onClick={() => handleRemoveInterest(interest)}
                                aria-label={`Remove ${interest}`}
                                className="text-blue font-medium text-blue-hover ml-1"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            </section>

            <section className="card">
                <h3 className="text-lg font-medium mb-2">Implicit Interests (Preview)</h3>
                <p className="text-subtle mb-3">
                    Automatically inferred interests from your search and click activity will appear here. You will be able to promote them to explicit interests.
                </p>
                <div className="text-muted italic">Coming soon…</div>
            </section>
        </div>
    );
}
