import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "../locales/en.json";

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

// Only English ships in the main bundle; other languages load on demand.
const LOADERS = {
  es: () => import(/* webpackChunkName: "locale-es" */ "../locales/es.json"),
  ht: () => import(/* webpackChunkName: "locale-ht" */ "../locales/ht.json"),
};

export async function changeLanguage(lng) {
  if (LOADERS[lng] && !i18n.hasResourceBundle(lng, "translation")) {
    const mod = await LOADERS[lng]();
    i18n.addResourceBundle(lng, "translation", stripTodo(mod.default || mod), true, true);
  }
  return i18n.changeLanguage(lng);
}

i18n.use(initReactI18next).init({
  resources: { en: { translation: en } },
  lng: "en",
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

if (saved !== "en" && LOADERS[saved]) changeLanguage(saved);

export default i18n;
