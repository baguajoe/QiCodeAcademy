// Global state in the 4Geeks flux.js style: getState returns { store, actions }.
import { api, adminApi, setAuthToken } from "../api";

const TOKEN_KEY = "qca.adminToken";
const safeStorage = (store) => {
  try {
    return window[store];
  } catch {
    return null;
  }
};

function readPref(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback;
  } catch {
    return fallback;
  }
}
function writePref(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode */
  }
}

const getState = ({ getStore, getActions, setStore }) => {
  const savedToken = safeStorage("sessionStorage")?.getItem(TOKEN_KEY) || null;
  if (savedToken) setAuthToken(savedToken);

  return {
    store: {
      settings: null, // public settings map
      siteImages: null, // { slot: { image_url, alt_text } }
      contentError: false,
      textSize: readPref("qca.textSize", "md"), // md | lg | xl
      contrast: readPref("qca.contrast", "normal"), // normal | high
      auth: { token: savedToken, user: null, checked: false },
    },
    actions: {
      // ---- Site content --------------------------------------------------
      loadSiteContent: async () => {
        const { settings, siteImages } = getStore();
        if (settings && siteImages) return;
        try {
          const [s, imgs] = await Promise.all([api.get("/settings"), api.get("/site-images")]);
          setStore({ settings: s, siteImages: imgs, contentError: false });
        } catch {
          setStore({ settings: getStore().settings || {}, siteImages: getStore().siteImages || {}, contentError: true });
        }
      },
      setting: (key, fallback = "") => {
        const s = getStore().settings;
        return (s && s[key]) || fallback;
      },
      refreshSiteContent: async () => {
        setStore({ settings: null, siteImages: null });
        await getActions().loadSiteContent();
      },

      // ---- Accessibility preferences -------------------------------------
      setTextSize: (size) => {
        document.documentElement.setAttribute("data-text-size", size);
        writePref("qca.textSize", size);
        setStore({ textSize: size });
      },
      setContrast: (mode) => {
        if (mode === "high") document.documentElement.setAttribute("data-contrast", "high");
        else document.documentElement.removeAttribute("data-contrast");
        writePref("qca.contrast", mode);
        setStore({ contrast: mode });
      },

      // ---- Admin auth (token in memory + sessionStorage) ------------------
      login: async (email, password) => {
        const data = await api.post("/auth/login", { email, password });
        setAuthToken(data.access_token);
        safeStorage("sessionStorage")?.setItem(TOKEN_KEY, data.access_token);
        setStore({ auth: { token: data.access_token, user: data.user, checked: true } });
        return data.user;
      },
      logout: () => {
        setAuthToken(null);
        safeStorage("sessionStorage")?.removeItem(TOKEN_KEY);
        setStore({ auth: { token: null, user: null, checked: true } });
      },
      checkAuth: async () => {
        const { auth } = getStore();
        if (!auth.token) {
          setStore({ auth: { ...auth, checked: true } });
          return null;
        }
        try {
          const user = await adminApi.get("/auth/me");
          setStore({ auth: { token: getStore().auth.token, user, checked: true } });
          return user;
        } catch {
          getActions().logout();
          return null;
        }
      },
    },
  };
};

export default getState;
