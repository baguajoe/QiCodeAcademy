import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useStore } from "./store/appContext";
import { shareImageUrl } from "./siteImages";

export const ORG = {
  name: "Qi Code Academy",
  legalName: "Qi Code Academy, Inc.",
  neighborhoods: ["Dorchester", "Roxbury", "Mattapan", "Hyde Park", "South End"],
};

export function orgJsonLd(settings = {}) {
  const origin = window.location.origin;
  const sameAs = ["social_facebook", "social_instagram", "social_youtube"].map((k) => settings[k]).filter(Boolean);
  const data = {
    "@context": "https://schema.org",
    "@type": "NGO",
    additionalType: "https://schema.org/NonprofitOrganization",
    name: ORG.name,
    legalName: ORG.legalName,
    url: origin,
    logo: `${origin}/img/og-default.png`,
    slogan: "Learn. Move. Create. Connect.",
    description:
      "Qi Code Academy empowers youth and older adults in Boston's inner-city communities through technology education, workforce development, wellness, community engagement, and research.",
    areaServed: ORG.neighborhoods.map((n) => ({ "@type": "Place", name: `${n}, Boston, MA` })),
    address: { "@type": "PostalAddress", addressLocality: "Boston", addressRegion: "MA", addressCountry: "US" },
  };
  if (sameAs.length) data.sameAs = sameAs;
  if (settings.org_contact_email) data.email = settings.org_contact_email;
  if (settings.org_contact_phone) data.telephone = settings.org_contact_phone;
  return data;
}

function add(tag, attrs, text) {
  const el = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  if (text) el.textContent = text;
  el.setAttribute("data-seo", "1");
  document.head.appendChild(el);
}

// Per-page <title>, meta description, Open Graph/Twitter tags, canonical and JSON-LD.
// Flask injects the same tags server-side for crawlers that don't run JavaScript.
export function useSeo({ title, description, imageSlot, image, type = "website", jsonLd = [], noindex = false }) {
  const { store } = useStore();
  const { t, i18n } = useTranslation();
  const settings = store.settings || {};
  const ldKey = JSON.stringify(jsonLd);

  useEffect(() => {
    const site = "Qi Code Academy";
    const fullTitle = title ? `${title} | ${site}` : `${site} — ${t("common.tagline")}`;
    const desc = description || t("seo.defaultDescription");
    const url = window.location.origin + window.location.pathname;
    const img = image
      ? image.startsWith("http") ? image : window.location.origin + image
      : shareImageUrl(imageSlot, store.siteImages);

    document.title = fullTitle;
    document.head.querySelectorAll("[data-seo]").forEach((n) => n.remove());
    add("meta", { name: "description", content: desc });
    if (noindex) add("meta", { name: "robots", content: "noindex, nofollow" });
    add("link", { rel: "canonical", href: url });
    add("meta", { property: "og:site_name", content: site });
    add("meta", { property: "og:type", content: type });
    add("meta", { property: "og:title", content: fullTitle });
    add("meta", { property: "og:description", content: desc });
    add("meta", { property: "og:url", content: url });
    add("meta", { property: "og:image", content: img });
    add("meta", { property: "og:locale", content: { en: "en_US", es: "es_US", ht: "ht_HT" }[i18n.language] || "en_US" });
    add("meta", { name: "twitter:card", content: "summary_large_image" });
    add("meta", { name: "twitter:title", content: fullTitle });
    add("meta", { name: "twitter:description", content: desc });
    add("meta", { name: "twitter:image", content: img });
    [orgJsonLd(settings), ...jsonLd].forEach((d) => add("script", { type: "application/ld+json" }, JSON.stringify(d)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title, description, imageSlot, image, type, ldKey, noindex, store.siteImages, store.settings, i18n.language]);
}
