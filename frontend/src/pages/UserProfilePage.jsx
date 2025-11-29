// src/pages/UserProfilePage.jsx
import React, {useState, useEffect, useCallback} from "react";
import {useNotifications} from "../notifications/NotificationProvider.jsx";
import {getCurrentUserId} from "../auth/auth.js";

const API_URL = "http://localhost:5000";
const IMPLICIT_SHOW_N = 10;

export default function UserProfilePage() {
    const {notify} = useNotifications();

    // Track current user dynamically
    const [userId] = useState(getCurrentUserId());
    const [explicitInterests, setExplicitInterests] = useState([]);
    const [implicitInterests, setImplicitInterests] = useState([]);
    const [implicitExclusions, setImplicitExclusions] = useState([]);
    const [newInterest, setNewInterest] = useState("");
    const [loadingSave, setLoadingSave] = useState(false);
    const [loadingImplicitRemove, setLoadingImplicitRemove] = useState(false);
    const [loadingClearExplicit, setLoadingClearExplicit] = useState(false);
    const [loadingClearImplicit, setLoadingClearImplicit] = useState(false);

    // fetch profile and populate both explicit and implicit sets
    const loadProfile = useCallback(() => {
        fetch(`${API_URL}/profiles/${userId}`)
            .then(res => res.ok ? res.json() : Promise.reject("Failed to load profile"))
            .then(profile => {
                setExplicitInterests(profile.explicit_interests || []);
                const sortedImplicit = Object.entries(profile.implicit_interests || {})
                    .sort(([, aWeight], [, bWeight]) => bWeight - aWeight)
                    .map(([keyword, weight]) => ({keyword, weight}));
                setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
                setImplicitExclusions(profile.implicit_exclusions || []);
            })
            .catch(err => {
                setExplicitInterests([]);
                setImplicitInterests([]);
                setImplicitExclusions([]);
                notify({type: "error", title: "Load failed", message: err.message || "Could not load profile"});
            });
    }, [userId, notify]);

    useEffect(() => {
        loadProfile();
    }, [loadProfile, userId]);

    const addInterest = () => {
        const trimmed = newInterest.trim();
        if (!trimmed) return;

        fetch(`${API_URL}/profiles/explicit/add`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({user_id: userId, keyword: trimmed, weight: 1.0})
        })
            .then(async res => {
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Add failed");
                setExplicitInterests(data.explicit_interests || []);
                notify({type: "success", title: "Added", message: `"${trimmed}" added`});
                loadProfile();
            })
            .catch(err => {
                notify({type: "error", title: "Add failed", message: err.message || "Could not add interest"});
            })
            .finally(() => setNewInterest(""));
    };

    const removeExplicitInterest = (keyword) => {
        fetch(`${API_URL}/profiles/explicit/remove`, {
            method: "DELETE",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({user_id: userId, keyword})
        })
            .then(async res => {
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Remove failed");
                setExplicitInterests(data.explicit_interests || []);
                notify({type: "success", title: "Removed", message: `"${keyword}" removed`});
                loadProfile();
            })
            .catch(err => {
                notify({type: "error", title: "Remove failed", message: err.message || "Could not remove interest"});
            });
    };

    // remove implicit interest (persistently suppress it)
    const removeImplicitInterest = async (keyword) => {
        setLoadingImplicitRemove(true);
        try {
            const res = await fetch(`${API_URL}/profiles/implicit/remove`, {
                method: "DELETE",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: userId, keyword})
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Remove failed");

            const sortedImplicit = Object.entries(data.implicit_interests || {})
                .sort(([, aWeight], [, bWeight]) => bWeight - aWeight)
                .map(([keyword, weight]) => ({keyword, weight}));

            setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
            setImplicitExclusions(data.implicit_exclusions || []);
            notify({
                type: "success",
                title: "Implicit removed",
                message: `"${keyword}" removed from implicit interests`
            });
        } catch (err) {
            notify({
                type: "error",
                title: "Remove failed",
                message: err.message || "Could not remove implicit interest"
            });
        } finally {
            setLoadingImplicitRemove(false);
        }
    };

    // undo the implicit exclusion (re-enable the keyword)
    const undoImplicitExclusion = async (keyword) => {
        setLoadingImplicitRemove(true);
        try {
            const res = await fetch(`${API_URL}/profiles/implicit/exclusion/remove`, {
                method: "DELETE",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: userId, keyword})
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Remove failed");

            const sortedImplicit = Object.entries(data.implicit_interests || {})
                .sort(([, aWeight], [, bWeight]) => bWeight - aWeight)
                .map(([keyword, weight]) => ({keyword, weight}));

            setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
            setImplicitExclusions(data.implicit_exclusions || []);

            notify({
                type: "success",
                title: "Interest restored",
                message: `"${keyword}" has been re-enabled and added back to your interests.`
            });
        } catch (err) {
            notify({type: "error", title: "Remove failed", message: err.message || "Could not remove exclusion"});
        } finally {
            setLoadingImplicitRemove(false);
        }
    };

    // BULK SAVE
    const saveWeights = async (opts = {showToast: true}) => {
        setLoadingSave(true);
        try {
            const res = await fetch(`${API_URL}/profiles/explicit/bulk_update`, {
                method: "PUT",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: userId, updates: explicitInterests})
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Save failed");
            setExplicitInterests(data.explicit_interests || []);
            if (opts.showToast) notify({type: "success", title: "Saved", message: "Interests updated"});
            loadProfile();
            return true;
        } catch (err) {
            notify({type: "error", title: "Save failed", message: err.message});
            return false;
        } finally {
            setLoadingSave(false);
        }
    };

    // ---- clear all explicit interests ----
    const clearAllExplicit = async () => {
        if (!explicitInterests || explicitInterests.length === 0) return;
        if (!window.confirm("Clear ALL explicit interests? This will delete them permanently.")) return;

        setLoadingClearExplicit(true);
        try {
            const res = await fetch(`${API_URL}/profiles/explicit/clear`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: userId})
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Clear failed");
            setExplicitInterests(data.explicit_interests || []);
            notify({type: "success", title: "Cleared", message: "All explicit interests removed"});
            loadProfile();
        } catch (err) {
            notify({
                type: "error",
                title: "Clear failed",
                message: err.message || "Could not clear explicit interests"
            });
        } finally {
            setLoadingClearExplicit(false);
        }
    };

    // ---- clear all implicit interests (move them to exclusions) ----
    const clearAllImplicit = async () => {
        if (!implicitInterests || implicitInterests.length === 0) return;
        if (!window.confirm("Move all implicit interests to exclusions? You can undo from the Exclusions section.")) return;

        setLoadingClearImplicit(true);
        try {
            const res = await fetch(`${API_URL}/profiles/implicit/clear`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id: userId})
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Clear failed");

            const sortedImplicit = Object.entries(data.implicit_interests || {})
                .sort(([, aWeight], [, bWeight]) => bWeight - aWeight)
                .map(([keyword, weight]) => ({keyword, weight}));

            setImplicitInterests(sortedImplicit.slice(0, IMPLICIT_SHOW_N));
            setImplicitExclusions(data.implicit_exclusions || []);
            notify({type: "success", title: "Cleared", message: "Implicit interests moved to exclusions"});
        } catch (err) {
            notify({
                type: "error",
                title: "Clear failed",
                message: err.message || "Could not clear implicit interests"
            });
        } finally {
            setLoadingClearImplicit(false);
        }
    };

    return (
        <div>
            <div className="flex items-center justify-between mb-3">
                <h2 className="text-2xl font-semibold">User Profile</h2>
                <span className="text-gray-600 italic">Current User: {userId}</span>
                <button
                    onClick={() => saveWeights({showToast: true})}
                    className="btn btn-secondary"
                    disabled={loadingSave}
                >
                    Quick Save
                </button>
            </div>

            <section className="card mb-6">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold">Explicit Interests</h3>
                    <div className="flex gap-2 items-center">
                        <button
                            onClick={clearAllExplicit}
                            className="btn btn-sm btn-danger"
                            disabled={loadingClearExplicit || explicitInterests.length === 0}
                            aria-label="Clear all explicit interests"
                        >
                            {loadingClearExplicit ? "Clearing…" : "Clear All"}
                        </button>
                    </div>
                </div>

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
                        <button onClick={addInterest} className="btn btn-primary btn-fixed">Add</button>
                    </div>
                </div>

                <div className="flex flex-col gap-2">
                    {explicitInterests.length === 0 && <p className="italic text-gray-500">No interests yet.</p>}
                    {explicitInterests.map(({keyword, weight}) => (
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
                                    setExplicitInterests(prev =>
                                        prev.map(i => i.keyword === keyword ? {...i, weight: newWeight} : i)
                                    );
                                }}
                            />
                            <span>{(weight ?? 0).toFixed(1)}</span>
                            <button onClick={() => removeExplicitInterest(keyword)}>×</button>
                        </div>
                    ))}
                </div>

                <div className="flex gap-2 mt-2">
                    <button
                        onClick={() => saveWeights({showToast: true})}
                        className="btn btn-primary btn-fixed"
                        disabled={loadingSave}
                    >
                        {loadingSave ? "Saving…" : "Save Changes"}
                    </button>
                </div>
            </section>

            <section className="card">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold">Implicit Interests</h3>
                    <div>
                        <button
                            onClick={clearAllImplicit}
                            className="btn btn-sm btn-warning"
                            disabled={loadingClearImplicit || implicitInterests.length === 0}
                            aria-label="Clear all implicit interests"
                        >
                            {loadingClearImplicit ? "Moving…" : "Clear All"}
                        </button>
                    </div>
                </div>

                {implicitInterests.length === 0 && (
                    <p className="text-gray-500 italic">No implicit interests yet.</p>
                )}

                {implicitInterests.length > 0 && (
                    <div className="flex flex-col gap-2">
                        {implicitInterests.map(({keyword, weight}) => (
                            <div key={keyword} className="flex items-center gap-2">
                                <span className="flex-1">{keyword}</span>
                                <span>{(weight ?? 0).toFixed(1)}</span>
                                <button
                                    onClick={() => removeImplicitInterest(keyword)}
                                    disabled={loadingImplicitRemove}
                                    title="Remove implicit interest"
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <section className="card">
                <h3 className="text-lg font-semibold mb-2">Implicit Exclusions</h3>

                {implicitExclusions.length === 0 && (
                    <p className="text-gray-500 italic">No implicit exclusions.</p>
                )}

                {implicitExclusions.length > 0 && (
                    <div className="flex flex-col gap-2">
                        {implicitExclusions.map((keyword) => (
                            <div key={keyword} className="flex items-center gap-2">
                                <span className="flex-1">{keyword}</span>

                                <button
                                    onClick={() => undoImplicitExclusion(keyword)}
                                    disabled={loadingImplicitRemove}
                                    title="Undo exclusion - re-enable this keyword"
                                    className="btn btn-sm btn-link text-blue-500"
                                >
                                    Undo
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}
