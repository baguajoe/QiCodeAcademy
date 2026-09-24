// Staff admin UI at /admin (JWT). English-only; large, simple, readable.
import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import "../../styles/admin.css";
import { adminApi, onUnauthorized } from "../api";
import { useStore } from "../store/appContext";
import { Loading } from "../component/common";
import { Logo } from "../component/Logo";
import { NAV_GROUPS, RESOURCES } from "./resources";
import { ResourceList } from "./ResourceList";
import { ResourceForm } from "./ResourceForm";
import { SettingsScreen } from "./SettingsScreen";
import { SiteImagesScreen } from "./SiteImagesScreen";
import { Dashboard } from "./Dashboard";

function useTitle(title) {
  useEffect(() => {
    document.title = `${title} · Admin · Qi Code Academy`;
    let m = document.querySelector('meta[name="robots"][data-admin]');
    if (!m) {
      m = Object.assign(document.createElement("meta"), { name: "robots", content: "noindex, nofollow" });
      m.setAttribute("data-admin", "1");
      document.head.appendChild(m);
    }
  }, [title]);
}
export { useTitle };

function Login() {
  const { store, actions } = useStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(location.state && location.state.expired ? "Your session ended. Please log in again." : "");
  const [busy, setBusy] = useState(false);
  useTitle("Log in");

  if (store.auth.token && store.auth.user) return <Navigate to="/admin" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await actions.login(email.trim(), password);
      navigate((location.state && location.state.from) || "/admin", { replace: true });
    } catch (err) {
      setError(err.status === 401 ? "That email and password don't match an active admin account."
        : err.status === 429 ? "Too many attempts. Please wait a minute and try again."
        : "We couldn't reach the server. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="admin-login" id="main-content">
      <form onSubmit={submit} className="admin-card" aria-labelledby="login-title">
        <div className="cluster" style={{ gap: "0.75rem", marginBottom: "1rem" }}>
          <Logo className="admin-logo" />
          <h1 id="login-title" style={{ margin: 0, fontSize: "1.6rem" }}>Staff log in</h1>
        </div>
        {error && <div className="alert alert-error" role="alert"><p>{error}</p></div>}
        <div className="field">
          <label htmlFor="login-email">Email</label>
          <input id="login-email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
        </div>
        <div className="field">
          <label htmlFor="login-password">Password</label>
          <input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn btn-lg btn-block" type="submit" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
        <p className="small muted" style={{ marginTop: "1rem" }}><Link to="/">← Back to the website</Link></p>
      </form>
    </main>
  );
}

function Sidebar({ counts, onNavigate }) {
  const { store, actions } = useStore();
  const badge = { registrations: counts.registrations_pending, "contact-messages": counts.unread_messages, "research-inquiries": counts.new_research_inquiries };
  return (
    <nav className="admin-nav" aria-label="Admin">
      <ul>
        <li><NavLink to="/admin" end onClick={onNavigate}>Dashboard</NavLink></li>
      </ul>
      {NAV_GROUPS.map((g) => (
        <div key={g}>
          <h2>{g}</h2>
          <ul>
            {Object.entries(RESOURCES).filter(([, r]) => r.group === g).map(([key, r]) => (
              <li key={key}>
                <NavLink to={`/admin/${key}`} onClick={onNavigate}>
                  {r.label}
                  {badge[key] ? <span className="count" aria-label={`${badge[key]} new`}>{badge[key]}</span> : null}
                </NavLink>
              </li>
            ))}
            {g === "Content" && <li><NavLink to="/admin/site-images" onClick={onNavigate}>Site photos</NavLink></li>}
            {g === "Settings" && <li><NavLink to="/admin/settings" onClick={onNavigate}>Site settings &amp; text</NavLink></li>}
          </ul>
        </div>
      ))}
      <ul className="admin-nav-foot">
        <li><a href="/" target="_blank" rel="noopener noreferrer">View website ↗</a></li>
        <li><a href="/flask-admin" target="_blank" rel="noopener noreferrer">Backup admin panel ↗</a></li>
        <li><button type="button" className="link-button" onClick={actions.logout}>Log out {store.auth.user ? `(${store.auth.user.email})` : ""}</button></li>
      </ul>
    </nav>
  );
}

function Shell() {
  const { store, actions } = useStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [counts, setCounts] = useState({});
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    onUnauthorized(() => {
      actions.logout();
      navigate("/admin/login", { replace: true, state: { expired: true, from: location.pathname } });
    });
    return () => onUnauthorized(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!store.auth.checked) actions.checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (store.auth.user) adminApi.get("/admin/dashboard").then(setCounts).catch(() => {});
  }, [store.auth.user, location.pathname]);

  useEffect(() => setNavOpen(false), [location.pathname]);

  if (!store.auth.token) return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />;
  if (!store.auth.user) return <div className="container"><Loading label="Checking your login…" /></div>;

  return (
    <div className="admin-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="admin-top">
        <Link to="/admin" className="admin-brand"><Logo className="admin-logo" /> <span>Qi Code Academy <strong>Admin</strong></span></Link>
        <button type="button" className="menu-toggle admin-menu" aria-expanded={navOpen} aria-controls="admin-sidebar" onClick={() => setNavOpen((o) => !o)}>
          {navOpen ? "Close" : "Menu"}
        </button>
      </header>
      <div className="admin-body">
        <aside id="admin-sidebar" className={`admin-sidebar ${navOpen ? "open" : ""}`}>
          <Sidebar counts={counts} onNavigate={() => setNavOpen(false)} />
        </aside>
        <main id="main-content" className="admin-main" tabIndex={-1}>
          <Routes>
            <Route index element={<Dashboard data={counts} />} />
            <Route path="settings" element={<SettingsScreen />} />
            <Route path="site-images" element={<SiteImagesScreen />} />
            <Route path=":resource" element={<ResourceList />} />
            <Route path=":resource/new" element={<ResourceForm />} />
            <Route path=":resource/:id" element={<ResourceForm />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function AdminApp() {
  return (
    <Routes>
      <Route path="login" element={<Login />} />
      <Route path="*" element={<Shell />} />
    </Routes>
  );
}
