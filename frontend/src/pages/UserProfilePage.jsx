// src/pages/UserProfilePage.jsx
import React, { useState, useEffect, useCallback } from "react";
import { useNotifications } from "../notifications/NotificationProvider.jsx";
import { getCurrentUserId } from "../auth/auth.js";

const API_URL = "http://localhost:5000";
const IMPLICIT_SHOW_N = 10;

export default function UserProfilePage() {
    const { notify } = useNotifications();

    const [userId] = useState(getCurrentUserId());
    const [explicitInterests, setExplicitInterests] = useState([]);
    const [implicitInterests, setImplicitInterests] = useState([]);
    const [implicitExclusions, setImplicitExclusions] = useState([]);
    const [newInterest, setNewInterest] = useState("");

    const [loadingSave, setLoadingSave] = useState(false);
    const [loadingImplicitRemove, setLoadingImplicitRemove] = useState(false);
    const [loadingClearExplicit, setLoadingClearExplicit] = useState(false);
    const [loadingClearImplicit, setLoadingClearImplicit] = useState(false);

    const loadProfile = useCallback(() => {
        fetch(`${API_URL}/profiles/${userId}`)
            .then(res => res.ok ? res.json() : Promise.reject("Failed to load profile"))
            .then(profile => {
                setExplicitInterests(profile.explicit_interests || []);

                const sortedImplicit = Object.entries(profile.implicit_interests || {})
                    .sort(([, a], [, b]) => b - a)
                    .map(([keyword, weight]) => ({ keyword, weight }));

                setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
                setImplicitExclusions(profile.implicit_exclusions || []);
            })
            .catch(() => {
                notify({ type: "error", title: "Load failed", message: "Could not load profile" });
                setExplicitInterests([]);
                setImplicitInterests([]);
                setImplicitExclusions([]);
            });
    }, [userId, notify]);

    useEffect(() => loadProfile(), [loadProfile]);

    const addInterest = () => {
        const trimmed = newInterest.trim();
        if (!trimmed) return;

        fetch(`${API_URL}/profiles/explicit/add`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, keyword: trimmed, weight: 1.0 })
        })
            .then(res => res.json().then(data => ({ ok: res.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) throw new Error(data.detail || "Add failed");
                setExplicitInterests(data.explicit_interests || []);
                loadProfile();
            })
            .catch(err => notify({ type: "error", title: "Add failed", message: err.message }))
            .finally(() => setNewInterest(""));
    };

    const removeExplicitInterest = (keyword) => {
        fetch(`${API_URL}/profiles/explicit/remove`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, keyword })
        })
            .then(res => res.json().then(data => ({ ok: res.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) throw new Error(data.detail || "Remove failed");
                setExplicitInterests(data.explicit_interests || []);
                loadProfile();
            })
            .catch(err =>
                notify({ type: "error", title: "Remove failed", message: err.message })
            );
    };

    const removeImplicitInterest = async (keyword) => {
        setLoadingImplicitRemove(true);
        try {
            const res = await fetch(`${API_URL}/profiles/implicit/remove`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, keyword })
            });
            const data = await res.json();
            const sortedImplicit = Object.entries(data.implicit_interests || {})
                .sort(([, a], [, b]) => b - a)
                .map(([k, w]) => ({ keyword: k, weight: w }));

            setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
            setImplicitExclusions(data.implicit_exclusions || []);
        } finally {
            setLoadingImplicitRemove(false);
        }
    };

    const undoImplicitExclusion = async (keyword) => {
        setLoadingImplicitRemove(true);
        try {
            const res = await fetch(`${API_URL}/profiles/implicit/exclusion/remove`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, keyword })
            });
            const data = await res.json();

            const sortedImplicit = Object.entries(data.implicit_interests || {})
                .sort(([, a], [, b]) => b - a)
                .map(([k, w]) => ({ keyword: k, weight: w }));

            setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
            setImplicitExclusions(data.implicit_exclusions || []);
        } finally {
            setLoadingImplicitRemove(false);
        }
    };

    const saveWeights = async () => {
        setLoadingSave(true);
        try {
            const res = await fetch(`${API_URL}/profiles/explicit/bulk_update`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, updates: explicitInterests })
            });
            const data = await res.json();
            setExplicitInterests(data.explicit_interests || []);
            loadProfile();
        } finally {
            setLoadingSave(false);
        }
    };

    return (
        <div className="profile-page container">

            {/* ================= EXPLICIT INTERESTS ================ */}
            <section className="profile-card">
                <h3 className="profile-section-title">Explicit Interest</h3>

                <input
                    type="text"
                    className="profile-input"
                    placeholder="Add new interest"
                    value={newInterest}
                    onChange={e => setNewInterest(e.target.value)}
                />

                <button onClick={addInterest} className="profile-add-btn">Add</button>

                <div className="profile-list">
                    {explicitInterests.length === 0 ? (
                        <p className="profile-empty-msg">No new interests</p>
                    ) : (
                        explicitInterests.map(({ keyword, weight }) => (
                            <div className="profile-row" key={keyword}>
                                <span className="profile-keyword">{keyword}</span>

                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.1"
                                    value={weight}
                                    className="profile-slider"
                                    onChange={(e) => {
                                        const w = parseFloat(e.target.value);
                                        setExplicitInterests(prev =>
                                            prev.map(i =>
                                                i.keyword === keyword ? { ...i, weight: w } : i
                                            )
                                        );
                                    }}
                                />

                                <span className="profile-score">{weight.toFixed(1)}</span>

                                <button
                                    className="profile-remove-btn"
                                    onClick={() => removeExplicitInterest(keyword)}
                                >
                                    ×
                                </button>
                            </div>
                        ))
                    )}
                </div>

                <button
                    className="profile-save-btn"
                    onClick={saveWeights}
                    disabled={loadingSave}
                >
                    {loadingSave ? "Saving…" : "Save Changes"}
                </button>
            </section>

            {/* ================= IMPLICIT INTERESTS ================ */}
            <section className="profile-card">
                <h3 className="profile-section-title">Implicit Interest</h3>

                <div className="profile-list">
                    {implicitInterests.length === 0 ? (
                        <p className="profile-empty-msg">No implicit interests yet</p>
                    ) : (
                        implicitInterests.map(({ keyword, weight }) => (
                            <div className="profile-row" key={keyword}>
                                <span className="profile-keyword">{keyword}</span>

                                <span className="profile-score">{weight.toFixed(1)}</span>

                                <button
                                    className="profile-remove-btn"
                                    onClick={() => removeImplicitInterest(keyword)}
                                    disabled={loadingImplicitRemove}
                                >
                                    ×
                                </button>

                                <button className="profile-upgrade-btn">Upgrade</button>
                            </div>
                        ))
                    )}
                </div>
            </section>

            {/* ================= IMPLICIT EXCLUSIONS ================ */}
            <section className="profile-card">
                <h3 className="profile-section-title">Implicit Exclusions</h3>

                <div className="profile-list">
                    {implicitExclusions.length === 0 ? (
                        <p className="profile-empty-msg">No implicit exclusions yet</p>
                    ) : (
                        implicitExclusions.map(keyword => (
                            <div className="profile-row" key={keyword}>
                                <span className="profile-keyword">{keyword}</span>

                                <button
                                    className="profile-undo-btn"
                                    onClick={() => undoImplicitExclusion(keyword)}
                                    disabled={loadingImplicitRemove}
                                >
                                    Undo
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </section>

        </div>
    );
}
