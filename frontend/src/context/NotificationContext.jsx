// // src/context/NotificationContext.jsx
// import React, { createContext, useContext, useState } from "react";
//
// const NotificationContext = createContext();
//
// export function NotificationProvider({ children }) {
//     const [messages, setMessages] = useState([]);
//
//     const notify = (message, type = "info", duration = 3000) => {
//         const id = Date.now();
//         setMessages(prev => [...prev, { id, message, type }]);
//         setTimeout(() => setMessages(prev => prev.filter(m => m.id !== id)), duration);
//     };
//
//     return (
//         <NotificationContext.Provider value={{ notify }}>
//             {children}
//             <div className="notification-container fixed top-4 right-4 space-y-2 z-50">
//                 {messages.map(m => (
//                     <div
//                         key={m.id}
//                         className={`rounded p-2 shadow text-white ${m.type === "success" ? "bg-green-500" : m.type === "error" ? "bg-red-500" : "bg-gray-500"}`}
//                     >
//                         {m.message}
//                     </div>
//                 ))}
//             </div>
//         </NotificationContext.Provider>
//     );
// }
//
// export const useNotifications = () => useContext(NotificationContext);
