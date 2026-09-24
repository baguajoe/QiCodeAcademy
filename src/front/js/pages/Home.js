import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { Photo, SiteImage, isSlotPlaceholder } from "../component/Photo";
import { EventCard, NewsCard } from "../component/Cards";
import { Empty, SectionHeader } from "../component/common";

function Hero() {
  const { t } = useTranslation();
  const { store } = useStore();
  const placeholder = isSlotPlaceholder("hero-home", store.siteImages);
  return (
    <section className={`hero ${placeholder ? "is-placeholder" : ""}`} aria-labelledby="hero-title">
      <div className="hero-media">
        <SiteImage slot="hero-home" sizes="100vw" priority ratio={null} />
      </div>
      <div className="container hero-content">
        <h1 id="hero-title">Qi Code Academy</h1>
        <p className="tagline">{t("common.tagline")}</p>
        <p className="mission">{t("home.missionShort")}</p>
        <div className="cluster">
          <a className="btn btn-lg btn-light" href="#divisions">{t("home.ctaPrograms")}</a>
          <Link className="btn btn-lg btn-donate" to="/donate">{t("home.ctaDonate")}</Link>
        </div>
      </div>
    </section>
  );
}

const DIVISION_CARDS = [
  { key: "youth", theme: "youth", slot: "home-card-youth", to: "/programs/youth" },
  { key: "senior", theme: "senior", slot: "home-card-seniors", to: "/programs/seniors" },
  { key: "research", theme: "research", slot: "home-card-research", to: "/research" },
];

function Divisions() {
  const { t } = useTranslation();
  return (
    <section className="section" id="divisions" aria-labelledby="divisions-title">
      <div className="container">
        <SectionHeader eyebrow={t("home.divisionsEyebrow")} title={t("home.divisionsTitle")} lead={t("home.divisionsLead")} id="divisions-title" />
        <div className="grid grid-3 division-cards">
          {DIVISION_CARDS.map((d) => (
            <article key={d.key} className={`card card-accent division-card theme-${d.theme}`}>
              <div className="card-media"><SiteImage slot={d.slot} sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw" ratio={null} /></div>
              <div className="card-body">
                <span className="motto">{t(`divisions.${d.key}.motto`)}</span>
                <h3>{t(`divisions.${d.key}.name`)}</h3>
                <p>{t(`divisions.${d.key}.summary`)}</p>
              </div>
              <div className="card-footer">
                <Link className="btn" to={d.to}>
                  {t("common.learnMore")}<span className="sr-only">: {t(`divisions.${d.key}.name`)}</span>
                </Link>
              </div>
            </article>
          ))}
        </div>
        <div className="inter-band theme-intergenerational" style={{ marginTop: "2rem" }}>
          <div>
            <span className="eyebrow">{t("divisions.intergenerational.motto")}</span>
            <h3>{t("home.interTitle")}</h3>
            <p style={{ margin: 0 }}>{t("home.interBody")}</p>
          </div>
          <div><Link className="btn" to="/programs/intergenerational">{t("home.interCta")}</Link></div>
        </div>
      </div>
    </section>
  );
}

export function Neighborhoods({ alt = true }) {
  const { t } = useTranslation();
  return (
    <section className={`section ${alt ? "section-alt" : ""}`} aria-labelledby="hoods-title">
      <div className="container">
        <SectionHeader title={t("neighborhoods.title")} lead={t("neighborhoods.lead")} center id="hoods-title" />
        <ul className="hoods">
          {t("neighborhoods.list", { returnObjects: true }).map((n) => <li key={n}>{n}</li>)}
        </ul>
      </div>
    </section>
  );
}

function UpcomingEvents() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/events", { params: { per_page: 3 } }), []);
  return (
    <section className="section" aria-labelledby="events-title">
      <div className="container">
        <div className="cluster" style={{ justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <h2 id="events-title" style={{ margin: 0 }}>{t("home.eventsTitle")}</h2>
          <Link to="/events">{t("home.allEvents")}</Link>
        </div>
        {data && data.items.length ? (
          <div className="grid grid-3">{data.items.map((e) => <EventCard key={e.id} event={e} />)}</div>
        ) : data ? (
          <Empty>{t("home.noEvents")}</Empty>
        ) : null}
      </div>
    </section>
  );
}

function ImpactStats() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/impact-stats"), []);
  if (!data || !data.items.length) return null;
  return (
    <section className="section section-accent" aria-labelledby="impact-title">
      <div className="container">
        <SectionHeader title={t("home.impactTitle")} center id="impact-title" />
        <ul className="stats">
          {data.items.map((s) => (
            <li className="stat" key={s.id}>
              <span className="value">{s.value}</span>
              <span className="label">{s.label}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function GalleryStrip() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/gallery", { params: { per_page: 6 } }), []);
  const items = data ? data.items : [];
  return (
    <section className="section" aria-labelledby="gallery-title">
      <div className="container">
        <div className="cluster" style={{ justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <h2 id="gallery-title" style={{ margin: 0 }}>{t("home.galleryTitle")}</h2>
          <Link to="/gallery">{t("home.galleryAll")}</Link>
        </div>
        <ul className="photo-grid photo-grid-6">
          {items.length
            ? items.map((p) => (
                <li key={p.id}>
                  <Link to="/gallery" aria-label={p.alt_text}>
                    <Photo src={p.image_url} alt={p.alt_text} sizes="(min-width: 72rem) 16vw, (min-width: 48rem) 33vw, 50vw" />
                  </Link>
                </li>
              ))
            : [0, 1, 2].map((i) => (
                <li key={i}>
                  <Photo ratio="1" placeholder={{ division: ["youth", "senior", "intergenerational"][i], subject: "Gallery photo (added in admin → Gallery)", size: "1200×1200" }} />
                </li>
              ))}
        </ul>
      </div>
    </section>
  );
}

function Ctas() {
  const { t } = useTranslation();
  return (
    <section className="section" aria-label={t("home.involvedTitle")}>
      <div className="container">
        <div className="cta-band">
          <div className="cta-item">
            <h2>{t("home.involvedTitle")}</h2>
            <p>{t("home.involvedBody")}</p>
            <Link className="btn btn-light" to="/get-involved">{t("home.involvedCta")}</Link>
          </div>
          <div className="cta-item">
            <h2>{t("home.donateTitle")}</h2>
            <p>{t("home.donateBody")}</p>
            <Link className="btn btn-donate" to="/donate">{t("home.donateCta")}</Link>
          </div>
        </div>
      </div>
    </section>
  );
}

function LatestNews() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/news", { params: { per_page: 3 } }), []);
  if (!data || !data.items.length) return null;
  return (
    <section className="section section-alt" aria-labelledby="news-title">
      <div className="container">
        <div className="cluster" style={{ justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <h2 id="news-title" style={{ margin: 0 }}>{t("home.newsTitle")}</h2>
          <Link to="/news">{t("home.allNews")}</Link>
        </div>
        <div className="grid grid-3">{data.items.map((p) => <NewsCard key={p.id} post={p} />)}</div>
      </div>
    </section>
  );
}

export default function Home() {
  useSeo({ imageSlot: "hero-home" });
  return (
    <>
      <Hero />
      <Divisions />
      <Neighborhoods />
      <UpcomingEvents />
      <ImpactStats />
      <GalleryStrip />
      <Ctas />
      <LatestNews />
    </>
  );
}
