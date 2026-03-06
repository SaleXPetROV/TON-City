import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Suppress wallet extension errors in console
const originalError = console.error;
console.error = (...args) => {
  const msg = args[0]?.toString() || '';
  // Suppress known extension conflicts
  if (msg.includes('Cannot redefine property: ethereum') ||
      msg.includes('evmAsk.js') ||
      msg.includes('chrome-extension://')) {
    return; // Silently ignore
  }
  originalError.apply(console, args);
};

// Global error handler for uncaught extension errors
window.addEventListener('error', (event) => {
  if (event.filename?.includes('chrome-extension://') ||
      event.message?.includes('Cannot redefine property')) {
    event.preventDefault();
    return false;
  }
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
