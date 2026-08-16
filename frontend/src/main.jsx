import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles/variables.css";
import "./styles/global.css";
import "./styles/animations.css";
createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
