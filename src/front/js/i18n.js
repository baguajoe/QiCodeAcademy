import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "../locales/en.json";
import es from "../locales/es.json";
import ht from "../locales/ht.json";

export const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "es", label: "Español", inProgress: true },
  { code: "ht", label: "Kreyòl ayisyen", inProgress: true },
];

// Scaffolded translations use "TODO" placeholders. Drop them so i18next falls
// back to English for anything not yet translated.
function stripTodo(obj) {
  const out = {};
  Object.entries(obj).forEach(([k, v]) => {
    if (Array.isArray(v)) {
      if (!v.some((x) => typeof x === "string" && x.startsWith("TODO"))) out[k] = v;
    } else if (v && typeof v === "object") out[k] = stripTodo(v);
    else if (typeof v === "string" && !v.startsWith("TODO")) out[k] = v;
  });
  return out;
}

let saved = "en";
try {
  saved = localStorage.getItem("qca.lang") || "en";
} catch {
  /* ignore */
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    es: { translation: stripTodo(es) },
    ht: { translation: stripTodo(ht) },
  },
  lng: LANGUAGES.some((l) => l.code === saved) ? saved : "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false }, // React escapes
  returnNull: false,
});

i18n.on("languageChanged", (lng) => {
  document.documentElement.setAttribute("lang", lng);
  try {
    localStorage.setItem("qca.lang", lng);
  } catch {
    /* ignore */
  }
});

export default i18n;
