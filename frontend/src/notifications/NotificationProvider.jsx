import React, { createContext, useContext, useReducer, useCallback, useEffect } from "react";
import "./notifications.css";

const NotificationContext = createContext(null);

let idCounter = 0;
const makeId = () => `${Date.now()}-${idCounter++}-${Math.floor(Math.random()*1000)}`;

const MAX_TOASTS = 5;
const DEFAULT_DURATION = 5000;

function reducer(state, action) {
    switch (action.type) {
        case "PUSH": {
            const next = [{ ...action.payload }, ...state];
            // enforce max
            return next.slice(0, MAX_TOASTS);
        }
        case "REMOVE":
            return state.filter(t => t.id !== action.id);
        case "CLEAR":
            return [];
        default:
            return state;
    }
}

export function NotificationProvider({ children }) {
    const [toasts, dispatch] = useReducer(reducer, []);

    const notify = useCallback(({ type = "info", title = "", message = "", duration = DEFAULT_DURATION }) => {
        const id = makeId();
        const toast = { id, type, title, message, duration };
        dispatch({ type: "PUSH", payload: toast });

        // return id so callers can manually remove if needed
        return id;
    }, []);

    const remove = useCallback((id) => dispatch({ type: "REMOVE", id }), []);
    const clear = useCallback(() => dispatch({ type: "CLEAR" }), []);

    return (
        <NotificationContext.Provider value={{ notify, remove, clear, toasts }}>
            {children}
            <NotificationContainer toasts={toasts} onRemove={remove} />
        </NotificationContext.Provider>
    );
}

export function useNotifications() {
    const ctx = useContext(NotificationContext);
    if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
    return ctx;
}

/* ---------- Internal visual component ---------- */

function NotificationContainer({ toasts, onRemove }) {
    // container fixed in top-right
    return (
        <div className="notif-container" aria-live="polite" aria-atomic="true">
            {toasts.map(t => (
                <Toast key={t.id} toast={t} onClose={() => onRemove(t.id)} />
            ))}
        </div>
    );
}

function Toast({ toast, onClose }) {
    const { id, type, title, message, duration } = toast;

    useEffect(() => {
        if (!duration || duration <= 0) return;
        const timer = setTimeout(() => onClose(id), duration);
        return () => clearTimeout(timer);
    }, [id, duration, onClose]);

    return (
        <div className={`notif-toast notif-${type}`} role="status" aria-live="polite">
            <div className="notif-body">
                {title && <div className="notif-title">{title}</div>}
                {message && <div className="notif-message">{message}</div>}
            </div>
            <button className="notif-close" onClick={() => onClose(id)} aria-label="Dismiss notification">×</button>
        </div>
    );
}
