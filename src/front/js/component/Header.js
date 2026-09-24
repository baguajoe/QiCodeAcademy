import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useStore } from "../store/appContext";
import { LANGUAGES, changeLanguage } from "../i18n";
import { Logo } from "./Logo";

function Caret() {
  return (
    <svg className="caret" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path d="M5.3 7.3a1 1 0 0 1 1.4 0L10 10.6l3.3-3.3a1 1 0 1 1 1.4 1.4l-4 4a1 1 0 0 1-1.4 0l-4-4a1 1 0 0 1 0-1.4z" />
    </svg>
  );
}

function MenuIcon({ open }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
      {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
    </svg>
  );
}

function UtilityBar() {
  const { t, i18n } = useTranslation();
  const { store, actions } = useStore();
  const sizes = [
    { id: "md", label: "A", aria: t("a11y.textStandard"), cls: "size-a1" },
    { id: "lg", label: "A+", aria: t("a11y.textLarger"), cls: "size-a2" },
    { id: "xl", label: "A++", aria: t("a11y.textLargest"), cls: "size-a3" },
  ];
  return (
    <section className="utility-bar" aria-label={t("a11y.settings")}>
      <div className="container">
        <div className="utility-group" role="group" aria-label={t("a11y.textSize")}>
          <span className="label" aria-hidden="true">{t("a11y.textSizeShort")}</span>
          {sizes.map((s) => (
            <button key={s.id} type="button" className={s.cls} aria-pressed={store.textSize === s.id}
              aria-label={s.aria} onClick={() => actions.setTextSize(s.id)}>
              {s.label}
            </button>
          ))}
        </div>
        <div className="utility-group">
          <button type="button" aria-pressed={store.contrast === "high"}
            onClick={() => actions.setContrast(store.contrast === "high" ? "normal" : "high")}>
            {t("a11y.highContrast")}
          </button>
        </div>
        <div className="utility-group">
          <label htmlFor="lang-select" className="label">{t("a11y.language")}</label>
          <select id="lang-select" value={i18n.language} onChange={(e) => changeLanguage(e.target.value)}>
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code} lang={l.code}>
                {l.label}{l.inProgress ? ` (${t("a11y.inProgress")})` : ""}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
}

export function Header() {
  const { t } = useTranslation();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [programsOpen, setProgramsOpen] = useState(false);
  const programsRef = useRef(null);
  const menuButtonRef = useRef(null);

  useEffect(() => {
    setMenuOpen(false);
    setProgramsOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key !== "Escape") return;
      if (programsOpen) {
        setProgramsOpen(false);
        programsRef.current?.querySelector("button")?.focus();
      } else if (menuOpen) {
        setMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };
    const onClick = (e) => {
      if (programsOpen && programsRef.current && !programsRef.current.contains(e.target)) setProgramsOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [programsOpen, menuOpen]);

  const programsActive = location.pathname.startsWith("/programs") || location.pathname.startsWith("/register");
  const links = [
    { to: "/research", label: t("nav.research") },
    { to: "/events", label: t("nav.events") },
    { to: "/get-involved", label: t("nav.getInvolved") },
    { to: "/contact", label: t("nav.contact") },
  ];

  return (
    <>
    <UtilityBar />
    <header className="site-header">
      <div className="container bar" style={{ position: "relative" }}>
        <Link to="/" className="logo" aria-label={t("nav.homeAria")}>
          <Logo />
          <span className="logo-text">
            <span className="logo-name">Qi Code Academy</span>
            <span className="logo-tag">{t("common.tagline")}</span>
          </span>
        </Link>

        <button ref={menuButtonRef} type="button" className="menu-toggle" aria-expanded={menuOpen}
          aria-controls="primary-nav" onClick={() => setMenuOpen((o) => !o)}>
          <MenuIcon open={menuOpen} />
          {menuOpen ? t("nav.close") : t("nav.menu")}
        </button>

        <nav id="primary-nav" className={`primary-nav ${menuOpen ? "open" : ""}`} aria-label={t("nav.main")}>
          <ul className="nav-list">
            <li><NavLink to="/" end>{t("nav.home")}</NavLink></li>
            <li><NavLink to="/about">{t("nav.about")}</NavLink></li>
            <li ref={programsRef}>
              <button type="button" className={`nav-button ${programsActive ? "is-active" : ""}`}
                aria-expanded={programsOpen} aria-controls="programs-submenu"
                onClick={() => setProgramsOpen((o) => !o)}>
                {t("nav.programs")} <Caret />
              </button>
              <ul id="programs-submenu" className="submenu" hidden={!programsOpen}>
                <li><NavLink to="/programs/youth">{t("nav.youth")}</NavLink></li>
                <li><NavLink to="/programs/seniors">{t("nav.seniors")}</NavLink></li>
                <li><NavLink to="/programs/intergenerational">{t("nav.intergenerational")}</NavLink></li>
              </ul>
            </li>
            {links.map((l) => (
              <li key={l.to}><NavLink to={l.to}>{l.label}</NavLink></li>
            ))}
            <li className="nav-donate">
              <NavLink to="/donate" className="btn btn-donate">{t("nav.donate")}</NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </header>
    </>
  );
}
