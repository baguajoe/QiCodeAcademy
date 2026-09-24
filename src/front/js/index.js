import { createRoot } from "react-dom/client";
import "../styles/tokens.css";
import "../styles/base.css";
import "../styles/layout.css";
import "../styles/components.css";
import "../styles/pages.css";
import "./i18n";
import { AppProvider } from "./store/appContext";
import Layout from "./layout";

createRoot(document.getElementById("app")).render(
  <AppProvider>
    <Layout />
  </AppProvider>
);
