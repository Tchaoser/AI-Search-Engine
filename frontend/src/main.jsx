import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import "./notifications/notifications.css";
import App from "./App.jsx";
import { NotificationProvider } from "./notifications/NotificationProvider.jsx";

createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <NotificationProvider>
            <App />
        </NotificationProvider>
    </React.StrictMode>
);
