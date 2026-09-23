import { useTranslation } from "react-i18next";
import { SiteImage, isSlotPlaceholder } from "./Photo";
import { useStore } from "../store/appContext";

export function Loading({ label }) {
  const { t } = useTranslation();
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label || t("common.loading")}</span>
    </div>
  );
}

export function ErrorNote({ error, onRetry }) {
  const { t } = useTranslation();
  const msg = error && error.status === 0 ? t("errors.network") : t("errors.generic");
  return (
    <div className="alert alert-error" role="alert">
      <p>{msg}</p>
      {onRetry && (
        <button type="button" className="btn btn-sm" onClick={onRetry}>{t("common.tryAgain")}</button>
      )}
    </div>
  );
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}

// Full-width division banner with a dark overlay so text always passes contrast.
export function PageBanner({ slot, motto, title, lead, children }) {
  const { store } = useStore();
  const placeholder = slot && isSlotPlaceholder(slot, store.siteImages);
  return (
    <section className={`banner ${slot ? "" : "banner-plain"} ${placeholder ? "is-placeholder" : ""}`}>
      {slot && (
        <div className="banner-media">
          <SiteImage slot={slot} sizes="100vw" priority ratio={null} />
        </div>
      )}
      <div className="container banner-content">
        {motto && <span className="motto">{motto}</span>}
        <h1>{title}</h1>
        {lead && <p className="lead">{lead}</p>}
        {children}
      </div>
    </section>
  );
}

export function SectionHeader({ eyebrow, title, lead, center, id }) {
  return (
    <div className={`section-header ${center ? "center" : ""}`}>
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h2 id={id}>{title}</h2>
      {lead && <p className="lead">{lead}</p>}
    </div>
  );
}

export function WellnessDisclaimer() {
  const { t } = useTranslation();
  return <p className="disclaimer"><strong>{t("footer.wellnessTitle")}</strong> {t("common.wellnessDisclaimer")}</p>;
}

// Honeypot input (named "website", per API.md). Off-screen and skipped by assistive tech.
export function Honeypot({ value, onChange }) {
  return (
    <div className="hp-field" aria-hidden="true">
      <label htmlFor="hp-website">Leave this field empty</label>
      <input id="hp-website" type="text" name="website" tabIndex={-1} autoComplete="off" value={value} onChange={onChange} />
    </div>
  );
}
