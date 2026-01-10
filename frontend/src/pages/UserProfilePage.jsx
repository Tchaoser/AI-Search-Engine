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

    const loadProfile = useCallback(() => {
        fetch(`${API_URL}/profiles/${userId}`)
            .then(res => res.ok ? res.json() : Promise.reject())
            .then(profile => {
                setExplicitInterests(profile.explicit_interests || []);

                const sortedImplicit = Object.entries(profile.implicit_interests || {})
                    .sort(([, a], [, b]) => b - a)
                    .map(([keyword, weight]) => ({ keyword, weight }));

                setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
                setImplicitExclusions(profile.implicit_exclusions || []);
            })
            .catch(() => {
                notify({
                    type: "error",
                    title: "Load failed",
                    message: "Could not load profile"
                });
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
            .then(() => loadProfile())
            .finally(() => setNewInterest(""));
    };

    const saveWeights = async () => {
        setLoadingSave(true);
        try {
            await fetch(`${API_URL}/profiles/explicit/bulk_update`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, updates: explicitInterests })
            });
            loadProfile();
        } finally {
            setLoadingSave(false);
        }
    };

    return (
        <div className="profile-page container">

            {/* Label for accessibility */}
            <h1 className="visually-hidden">User Profile</h1>

            {/* ================= EXPLICIT INTERESTS ================= */}
            <section className="profile-card">
                <h3 className="profile-section-title">Explicit Interest</h3>

                <label htmlFor="new-interest" className="visually-hidden">
                    Add a new explicit interest
                </label>

                <input
                    id="new-interest"
                    type="text"
                    className="profile-input"
                    placeholder="Add new interest"
                    value={newInterest}
                    onChange={e => setNewInterest(e.target.value)}
                />

                <button onClick={addInterest} className="profile-add-btn">
                    Add
                </button>

                <div className="profile-list">
                    {explicitInterests.map(({ keyword, weight }) => (
                        <div className="profile-row" key={keyword}>
                            <span className="profile-keyword">{keyword}</span>

                            <label
                                htmlFor={`weight-${keyword}`}
                                className="visually-hidden"
                            >
                                Interest weight for {keyword}
                            </label>

                            <input
                                id={`weight-${keyword}`}
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
                                            i.keyword === keyword
                                                ? { ...i, weight: w }
                                                : i
                                        )
                                    );
                                }}
                            />

                            <span className="profile-score">
                                {weight.toFixed(1)}
                            </span>

                            <button
                                className="profile-remove-btn"
                                aria-label={`Remove ${keyword} from explicit interests`}
                                onClick={() => {
                                    fetch(`${API_URL}/profiles/explicit/remove`, {
                                        method: "DELETE",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({ user_id: userId, keyword })
                                    }).then(loadProfile);
                                }}
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>

                <button
                    className="profile-save-btn"
                    onClick={saveWeights}
                    disabled={loadingSave}
                >
                    {loadingSave ? "Saving…" : "Save Changes"}
                </button>
            </section>

            {/* ================= IMPLICIT INTERESTS ================= */}
            <section className="profile-card">
                <h3 className="profile-section-title">Implicit Interest</h3>

                <div className="profile-list">
                    {implicitInterests.map(({ keyword, weight }) => (
                        <div className="profile-row" key={keyword}>
                            <span className="profile-keyword">{keyword}</span>
                            <span className="profile-score">{weight.toFixed(1)}</span>

                            <button
                                className="profile-remove-btn"
                                aria-label={`Exclude ${keyword} from implicit interests`}
                                disabled={loadingImplicitRemove}
                                onClick={() => {
                                    fetch(`${API_URL}/profiles/implicit/remove`, {
                                        method: "DELETE",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({ user_id: userId, keyword })
                                    }).then(loadProfile);
                                }}
                            >
                                ×
                            </button>

                            <button
                                className="profile-upgrade-btn"
                                aria-label={`Upgrade ${keyword} to explicit interest`}
                                disabled={loadingImplicitRemove}
                                onClick={() => {
                                    fetch(`${API_URL}/profiles/implicit/upgrade`, {
                                        method: "PUT",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({ user_id: userId, keyword })
                                    }).then(loadProfile);
                                }}
                            >
                                Upgrade
                            </button>
                        </div>
                    ))}
                </div>
            </section>

            {/* ================= IMPLICIT EXCLUSIONS ================= */}
            <section className="profile-card">
                <h3 className="profile-section-title">Implicit Exclusions</h3>

                <div className="profile-list">
                    {implicitExclusions.map(keyword => (
                        <div className="profile-row" key={keyword}>
                            <span className="profile-keyword">{keyword}</span>

                            <button
                                className="profile-undo-btn"
                                aria-label={`Undo exclusion of ${keyword}`}
                                onClick={() => {
                                    fetch(`${API_URL}/profiles/implicit/exclusion/remove`, {
                                        method: "DELETE",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({ user_id: userId, keyword })
                                    }).then(loadProfile);
                                }}
                            >
                                Undo
                            </button>
                        </div>
                    ))}
                </div>
            </section>

        </div>
    );
}
