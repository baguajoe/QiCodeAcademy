import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useStore } from "../store/appContext";
import { Logo } from "./Logo";

export function Footer() {
  const { t } = useTranslation();
  const { actions } = useStore();
  const socials = [
    { key: "social_facebook", label: "Facebook" },
    { key: "social_instagram", label: "Instagram" },
    { key: "social_youtube", label: "YouTube" },
  ].filter((s) => actions.setting(s.key));
  const email = actions.setting("org_contact_email");
  const phone = actions.setting("org_contact_phone");
  const taxStatus = actions.setting("tax_status");

  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-top">
          <div>
            <p className="cluster" style={{ gap: "0.75rem" }}>
              <Logo className="footer-logo" />
              <span>
                <strong style={{ fontSize: "1.2rem" }}>Qi Code Academy</strong>
                <br />
                {t("common.tagline")}
              </span>
            </p>
            <p>{t("footer.blurb")}</p>
            {(email || phone) && (
              <p>
                {email && (<>{t("footer.email")}: <a href={`mailto:${email}`}>{email}</a><br /></>)}
                {phone && (<>{t("footer.phone")}: <a href={`tel:${phone.replace(/[^\d+]/g, "")}`}>{phone}</a></>)}
              </p>
            )}
          </div>
          <nav aria-label={t("footer.exploreNav")}>
            <h2>{t("footer.explore")}</h2>
            <ul>
              <li><Link to="/news">{t("nav.news")}</Link></li>
              <li><Link to="/gallery">{t("nav.gallery")}</Link></li>
              <li><Link to="/events">{t("nav.events")}</Link></li>
              <li><Link to="/get-involved">{t("nav.getInvolved")}</Link></li>
              <li><Link to="/donate">{t("nav.donate")}</Link></li>
              <li><Link to="/privacy">{t("nav.privacy")}</Link></li>
              <li><Link to="/terms">{t("nav.terms")}</Link></li>
              <li><Link to="/photo-credits">{t("nav.photoCredits")}</Link></li>
            </ul>
          </nav>
          <div>
            <h2>{t("footer.connect")}</h2>
            {socials.length ? (
              <ul>
                {socials.map((s) => (
                  <li key={s.key}>
                    <a href={actions.setting(s.key)} target="_blank" rel="noopener noreferrer">
                      {s.label}<span className="sr-only"> ({t("common.opensNewTab")})</span>
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p>{t("footer.socialSoon")}</p>
            )}
            <p><Link to="/contact">{t("footer.contactUs")}</Link></p>
          </div>
        </div>
        <div className="footer-legal">
          <p className="footer-note"><strong>{t("footer.wellnessTitle")}</strong> {t("common.wellnessDisclaimer")}</p>
          {taxStatus && <p>{taxStatus}</p>}
          <p>© {new Date().getFullYear()} Qi Code Academy, Inc. {t("footer.rights")}</p>
        </div>
      </div>
    </footer>
  );
}
