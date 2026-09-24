import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useStore } from "../store/appContext";
import { SiteImage } from "./Photo";
import { textBlocks } from "../format";
import { FOUNDER_CREDENTIALS, FOUNDER_FULL_BIO, FOUNDER_NAME, FOUNDER_ROLE, FOUNDER_SHORT_BIO } from "../founderContent";

// Founder data: TeamMember (bio, editable) + settings (full bio, credentials), with verbatim fallbacks.
export function useFounder(team) {
  const { actions } = useStore();
  const member = (team || []).find((m) => m.name === FOUNDER_NAME) ||
    (team || []).find((m) => (m.role_title || "").toLowerCase().startsWith("founder"));
  return {
    member,
    name: member?.name || FOUNDER_NAME,
    role: member?.role_title || FOUNDER_ROLE,
    shortBio: member?.bio || FOUNDER_SHORT_BIO,
    fullBio: actions.setting("founder_full_bio", FOUNDER_FULL_BIO),
    credentials: actions.setting("founder_credentials", FOUNDER_CREDENTIALS)
      .split("\n").map((s) => s.trim()).filter(Boolean),
  };
}

export function Paragraphs({ text, headingLevel = 2 }) {
  const H = `h${headingLevel}`;
  return textBlocks(text).map((b, i) => (b.type === "h" ? <H key={i}>{b.text}</H> : <p key={i}>{b.text}</p>));
}

// "As featured in" — outlet names as plain text; they become links once staff add the URLs.
export function PressStrip() {
  const { t } = useTranslation();
  const { actions } = useStore();
  const outlets = [
    { name: "The Boston Globe", url: actions.setting("press_globe_url") },
    { name: "WCVB Channel 5 Chronicles", url: actions.setting("press_wcvb_url") },
  ];
  return (
    <section className="press-strip" aria-label={t("about.pressLabel")}>
      <span className="press-label">{t("about.pressLabel")}</span>
      {outlets.map((o) =>
        o.url ? (
          <a key={o.name} className="press-name" href={o.url} target="_blank" rel="noopener noreferrer">
            {o.name}<span className="sr-only"> ({t("common.opensNewTab")})</span>
          </a>
        ) : (
          <span key={o.name} className="press-name">{o.name}</span>
        )
      )}
    </section>
  );
}

export function CredentialsList({ items, compact }) {
  return (
    <ul className={`credentials ${compact ? "credentials-compact" : ""}`}>
      {items.map((c) => <li key={c}>{c}</li>)}
    </ul>
  );
}

export function FounderCard({ founder, headingLevel = 3, showCredentialsToggle = false }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const H = `h${headingLevel}`;
  return (
    <article className="founder-card theme-senior">
      <SiteImage slot="founder-portrait" sizes="(min-width: 48rem) 18rem, 100vw" />
      <div>
        <H style={{ marginBottom: "0.25rem" }}>{founder.name}</H>
        <p className="founder-role">{founder.role}</p>
        <Paragraphs text={founder.shortBio} />
        <div className="cluster">
          <Link className="btn" to="/about/founder">
            {t("common.readMore")}<span className="sr-only"> {t("about.readMoreFounder")}</span>
          </Link>
          {showCredentialsToggle && (
            <button type="button" className="btn btn-outline" aria-expanded={open}
              aria-controls="founder-credentials" onClick={() => setOpen((o) => !o)}>
              {open ? t("about.credentialsHide") : t("about.credentialsToggle")}
            </button>
          )}
        </div>
        {showCredentialsToggle && (
          <div id="founder-credentials" hidden={!open} style={{ marginTop: "1rem" }}>
            <CredentialsList items={founder.credentials} />
          </div>
        )}
      </div>
    </article>
  );
}
