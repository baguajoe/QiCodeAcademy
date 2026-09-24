import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { SiteImage } from "../component/Photo";
import { CredentialsList, Paragraphs, PressStrip, useFounder } from "../component/Founder";

export default function Founder() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/team"), []);
  const founder = useFounder(data ? data.items : []);
  const firstParagraph = founder.shortBio.split(/\n\s*\n/)[0];

  useSeo({
    title: `${founder.name}, ${founder.role}`,
    description: firstParagraph.length > 300 ? firstParagraph.slice(0, 297) + "…" : firstParagraph,
    imageSlot: "founder-portrait",
    type: "profile",
    jsonLd: [{
      "@context": "https://schema.org",
      "@type": "Person",
      name: founder.name,
      jobTitle: founder.role,
      description: firstParagraph,
      url: `${window.location.origin}/about/founder`,
      worksFor: { "@type": "NGO", name: "Qi Code Academy", legalName: "Qi Code Academy, Inc.", url: window.location.origin },
    }],
  });

  return (
    <div className="theme-senior">
      <section className="section">
        <div className="container">
          <nav className="breadcrumb" aria-label="Breadcrumb">
            <Link to="/about">← {t("founder.backToAbout")}</Link>
          </nav>
          <div className="founder-page">
            <aside className="founder-aside">
              <SiteImage slot="founder-portrait" sizes="(min-width: 56rem) 22rem, 100vw" priority />
            </aside>
            <div className="prose">
              <h1 style={{ marginBottom: "0.25rem" }}>{founder.name}</h1>
              <p className="founder-role" style={{ fontSize: "1.2rem" }}>{founder.role}</p>
              <Paragraphs text={founder.shortBio} />
              <Paragraphs text={founder.fullBio} headingLevel={2} />
              <h2>{t("founder.credentialsTitle")}</h2>
              <CredentialsList items={founder.credentials} />
              <figure style={{ margin: "2rem 0" }}>
                <SiteImage slot="founder-teaching" sizes="(min-width: 56rem) 44rem, 100vw" />
                <figcaption className="muted small" style={{ marginTop: "0.5rem" }}>{t("founder.teachingCaption")}</figcaption>
              </figure>
              <PressStrip />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
