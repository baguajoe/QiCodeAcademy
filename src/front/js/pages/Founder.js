import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { OptionalSiteImage, SiteImage } from "../component/Photo";
import { CredentialsList, Paragraphs, PressStrip, useFounder } from "../component/Founder";

export default function Founder() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/team"), []);
  const founder = useFounder(data ? data.items : []);
  // Split the full bio into its "## " sections so a photo can follow a matching section.
  const sections = founder.fullBio.split(/\n(?=## )/).map((x) => x.trim()).filter(Boolean);
  const sectionPhoto = (text) => {
    const heading = (text.match(/^## (.+)$/m) || [])[1] || "";
    if (/lineage/i.test(heading)) return { slot: "founder-prague-group", caption: t("founder.pragueCaption") };
    if (/massage|bodywork/i.test(heading)) return { slot: "founder-graduation", caption: t("founder.graduationCaption") };
    return null;
  };
  const paragraphs = founder.shortBio.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  const firstParagraph = paragraphs[0] || "";

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
      description: paragraphs.join(" "),
      url: `${window.location.origin}/about/founder`,
      worksFor: { "@type": "NGO", name: "Qi Code Academy", legalName: "Qi Code Academy, Inc.", url: window.location.origin },
    }],
  });

  return (
    <div className="theme-senior">
      <section className="section">
        <div className="container">
          <nav className="breadcrumb" aria-label={t("common.breadcrumb")}>
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
              {/* Teaching photo at the top, after the portrait and intro. */}
              <OptionalSiteImage slot="founder-teaching" sizes="(min-width: 56rem) 44rem, 100vw" ratio="16 / 9"
                caption={t("founder.teachingCaption")} className="founder-teaching" />
              {sections.map((section) => {
                const photo = sectionPhoto(section);
                return (
                  <div key={section.slice(0, 40)}>
                    <Paragraphs text={section} headingLevel={2} />
                    {photo && (
                      <OptionalSiteImage slot={photo.slot} sizes="(min-width: 56rem) 44rem, 100vw" ratio={null}
                        caption={photo.caption} />
                    )}
                  </div>
                );
              })}
              <h2>{t("founder.credentialsTitle")}</h2>
              <CredentialsList items={founder.credentials} />
              <PressStrip />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
