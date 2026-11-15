import React from "react";
import ReactDOM from "react-dom/client";
import "leaflet/dist/leaflet.css";
// Tipografia Folha-gota (servida junto com o app, funciona sem internet)
import "@fontsource/young-serif/400.css";
import "@fontsource/eb-garamond/400-italic.css";
import "@fontsource/work-sans/400.css";
import "@fontsource/work-sans/500.css";
import "@fontsource/work-sans/600.css";
import "./styles.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
