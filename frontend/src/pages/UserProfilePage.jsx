import React, { useState, useEffect } from "react";

const API_URL = "http://localhost:5000";
const USER_ID = "guest"; // hardcoded for now

export default function UserProfilePage() {
    const [interests, setInterests] = useState([]);
    const [newInterest, setNewInterest] = useState("");

    // fetch interests from backend
    useEffect(() => {
        fetch(`${API_URL}/profiles/${USER_ID}`)
            .then(res => res.json())
            .then(profile => setInterests(profile.explicit_interests || []))
            .catch(() => setInterests([]));
    }, []);

    const addInterest = () => {
        const trimmed = newInterest.trim();
        if (!trimmed) return;
        fetch(`${API_URL}/profiles/explicit/add`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: USER_ID, keyword: trimmed, weight: 1.0 })
        })
            .then(res => res.json())
            .then(profile => setInterests(profile.explicit_interests))
            .finally(() => setNewInterest(""));
    };

    const removeInterest = (keyword) => {
        fetch(`${API_URL}/profiles/explicit/remove`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: USER_ID, keyword })
        })
            .then(res => res.json())
            .then(profile => setInterests(profile.explicit_interests));
    };

    // ---- BULK SAVE: sends all slider weights at once ----
    const saveWeights = () => {
        // POST all interests to bulk_update endpoint
        fetch(`${API_URL}/profiles/explicit/bulk_update`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: USER_ID, updates: interests })
        })
            .then(res => res.json())
            .then(profile => setInterests(profile.explicit_interests));
    };

    return (
        <div>
            <h2 className="text-2xl font-semibold mb-3">User Profile</h2>
            <section className="card mb-6">
                <h3 className="text-lg font-medium mb-2">Explicit Interests</h3>
                <div className="flex flex-col gap-2 mb-4">
                    <input
                        type="text"
                        placeholder="Add new interest"
                        value={newInterest}
                        onChange={(e) => setNewInterest(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addInterest())}
                        className="input"
                    />
                    <button onClick={addInterest} className="btn btn-primary">Add</button>
                </div>

                <div className="flex flex-col gap-2">
                    {interests.length === 0 && <p className="italic text-gray-500">No interests yet.</p>}
                    {interests.map(({ keyword, weight }) => (
                        <div key={keyword} className="flex items-center gap-2">
                            <span className="flex-1">{keyword}</span>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={weight}
                                onChange={(e) => {
                                    const newWeight = parseFloat(e.target.value);
                                    // update local state only; backend is updated on save button press
                                    setInterests(prev =>
                                        prev.map(i => i.keyword === keyword ? { ...i, weight: newWeight } : i)
                                    );
                                }}
                            />
                            <span>{weight.toFixed(1)}</span>
                            <button onClick={() => removeInterest(keyword)} className="text-red-500 ml-2">×</button>
                        </div>
                    ))}
                </div>

                {/* Save all weights at once to reduce lag and backend requests */}
                <button onClick={saveWeights} className="btn btn-primary mt-4">
                    Save Changes
                </button>
            </section>

            <section className="card">
                <h3 className="text-lg font-medium mb-2">Implicit Interests (Preview)</h3>
                <p className="text-gray-500 italic">Coming soon…</p>
            </section>
        </div>
    );
}
