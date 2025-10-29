// src/pages/UserProfilePage.jsx
import React, { useState, useEffect } from "react";
import { useNotifications } from "../notifications/NotificationProvider.jsx";

const API_URL = "http://localhost:5000";
const USER_ID = "guest"; // hardcoded for now

export default function UserProfilePage() {
    const { notify } = useNotifications();

    const [interests, setInterests] = useState([]);
    const [newInterest, setNewInterest] = useState("");
    const [loadingSave, setLoadingSave] = useState(false);

    // fetch interests from backend
    useEffect(() => {
        fetch(`${API_URL}/profiles/${USER_ID}`)
            .then(res => {
                if (!res.ok) throw new Error("Failed to load profile");
                return res.json();
            })
            .then(profile => setInterests(profile.explicit_interests || []))
            .catch(err => {
                setInterests([]);
                notify({ type: "error", title: "Load failed", message: err.message || "Could not load profile" });
            });
    }, [notify]);

    const addInterest = () => {
        const trimmed = newInterest.trim();
        if (!trimmed) return;

        fetch(`${API_URL}/profiles/explicit/add`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: USER_ID, keyword: trimmed, weight: 1.0 })
        })
            .then(async res => {
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Add failed");
                setInterests(data.explicit_interests || []);
                notify({ type: "success", title: "Added", message: `"${trimmed}" added` });
            })
            .catch(err => {
                notify({ type: "error", title: "Add failed", message: err.message || "Could not add interest" });
            })
            .finally(() => setNewInterest(""));
    };

    const removeInterest = (keyword) => {
        fetch(`${API_URL}/profiles/explicit/remove`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: USER_ID, keyword })
        })
            .then(async res => {
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Remove failed");
                setInterests(data.explicit_interests || []);
                notify({ type: "success", title: "Removed", message: `"${keyword}" removed` });
            })
            .catch(err => {
                notify({ type: "error", title: "Remove failed", message: err.message || "Could not remove interest" });
            });
    };

    // ---- BULK SAVE: sends all slider weights at once ----
    const saveWeights = async (opts = { showToast: true }) => {
        setLoadingSave(true);
        try {
            const res = await fetch(`${API_URL}/profiles/explicit/bulk_update`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: USER_ID, updates: interests })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Save failed");
            setInterests(data.explicit_interests || []);
            if (opts.showToast) notify({ type: "success", title: "Saved", message: "Interests updated" });
            return true;
        } catch (err) {
            notify({ type: "error", title: "Save failed", message: err.message });
            return false;
        } finally {
            setLoadingSave(false);
        }
    };

    return (
        <div>
            <div className="flex items-center justify-between mb-3">
                <h2 className="text-2xl font-semibold">User Profile</h2>
                <button
                    onClick={() => saveWeights({ showToast: true })}
                    className="btn btn-secondary"
                    disabled={loadingSave}
                >
                    Quick Save
                </button>
            </div>
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
                    <div className="flex gap-2">
                        <button
                            onClick={addInterest}
                            className="btn btn-primary btn-fixed"
                        >
                            Add
                        </button>
                    </div>
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
                                    setInterests(prev =>
                                        prev.map(i => i.keyword === keyword ? { ...i, weight: newWeight } : i)
                                    );
                                }}
                            />
                            <span>{(weight ?? 0).toFixed(1)}</span>
                            <button onClick={() => removeInterest(keyword)} className="text-red-500 ml-2">×</button>
                        </div>
                    ))}
                </div>

                <div className="flex gap-2 mt-2">
                    <button
                        onClick={() => saveWeights({ showToast: true })}
                        className="btn btn-primary btn-fixed"
                        disabled={loadingSave}
                    >
                        {loadingSave ? "Saving…" : "Save Changes"}
                    </button>
                </div>
            </section>


            <section className="card">
                <h3 className="text-lg font-medium mb-2">Implicit Interests (Preview)</h3>
                <p className="text-gray-500 italic">Coming soon…</p>
            </section>
        </div>
    );
}
