import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { Photo, SiteImage, isSlotPlaceholder } from "../component/Photo";
import { EventCard, NewsCard } from "../component/Cards";
import { SectionHeader, useSettingText } from "../component/common";
import { BaguaMotif } from "../component/Logo";

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
        <p className="mission-history"><Link to="/about#history">{t("home.historyLine")}</Link></p>
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
      </div>
    </section>
  );
}

// Senior Wellness Day band: text left, photo right (alternates with the Baguazhang band above,
// whose photo is on the left); on phones the photo comes first. Uses the Wellness Day page's hero
// photo slot, so an admin upload (with its alt text and credit) carries over. Badge = wellness_day_status;
// the date line appears only once wellness_day_date is set.
const WD_CHIPS = [
  { key: "wellnessDayChipMovement", icon: "M12 3a9 9 0 1 0 0 18 4.5 4.5 0 0 1 0-9 4.5 4.5 0 0 0 0-9Zm0 4.5a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4Zm0 9a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4Z" },
  { key: "wellnessDayChipCare", icon: "M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z" },
  { key: "wellnessDayChipMarket", icon: "M4 9h16l-1.2-4H5.2L4 9Zm0 0v1.5a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0V9M5.5 13v7h13v-7M10 20v-4h4v4" },
];

function WellnessDayCard() {
  const { t } = useTranslation();
  const { actions } = useStore();
  const status = useSettingText()("wellness_day_status", "wellnessDay.statusDefault");
  const date = actions.setting("wellness_day_date").trim();
  return (
    <section className="section wd-home theme-senior" aria-labelledby="wd-home-title">
      <div className="container wd-home-inner">
        <div className="wd-home-body">
          <span className="badge badge-solid">{status}</span>
          <h2 id="wd-home-title">{t("home.wellnessDayTitle")}</h2>
          {date && <p className="wd-home-date">{date}</p>}
          <p>{t("home.wellnessDayText")}</p>
          <ul className="wd-home-chips">
            {WD_CHIPS.map((c) => (
              <li key={c.key}>
                <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">
                  <path d={c.icon} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {t(`home.${c.key}`)}
              </li>
            ))}
          </ul>
          <Link className="btn btn-lg" to="/programs/seniors/wellness-day">
            {t("home.wellnessDayCta")}<span className="sr-only">: {t("home.wellnessDayTitle")}</span>
          </Link>
        </div>
        <div className="wd-home-media">
          <SiteImage slot="seniors-banner" ratio="4 / 3" sizes="(min-width: 56rem) 45vw, 100vw" position="center 45%" />
        </div>
      </div>
    </section>
  );
}

function Intergenerational() {
  const { t } = useTranslation();
  return (
    <section className="section" aria-labelledby="inter-title">
      <div className="container">
        <div className="inter-band theme-intergenerational">
          <div>
            <span className="eyebrow">{t("divisions.intergenerational.motto")}</span>
            <h2 id="inter-title">{t("home.interTitle")}</h2>
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

// Signature program band. Title/text are editable in Admin → Site settings; while they
// still match the English default, the translated copy is shown instead.
function FeaturedProgram() {
  const { t } = useTranslation();
  const fromSetting = useSettingText();
  const title = fromSetting("featured_program_title", "home.featuredTitle");
  return (
    <section className="section section-dark theme-research featured-program" aria-labelledby="featured-title">
      <BaguaMotif className="featured-motif" />
      <div className="container featured-inner">
        <div className="featured-media">
          <SiteImage slot="research-banner" ratio="4 / 3" sizes="(min-width: 56rem) 45vw, 100vw" />
        </div>
        <div className="featured-body">
          <span className="eyebrow">{t("home.featuredEyebrow")}</span>
          <h2 id="featured-title">{title}</h2>
          <p>{fromSetting("featured_program_text", "home.featuredText")}</p>
          <div className="cluster">
            <Link className="btn btn-lg btn-light" to="/research#healthy-aging">
              {t("home.featuredLearnMore")}<span className="sr-only">: {title}</span>
            </Link>
            <Link className="btn btn-lg btn-ghost-light" to="/programs/seniors">{t("home.featuredJoin")}</Link>
          </div>
        </div>
      </div>
    </section>
  );
}

// Hidden entirely until an admin publishes an upcoming event (never an empty box).
function UpcomingEvents() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/events", { params: { per_page: 3 } }), []);
  if (!data || !data.items.length) return null;
  return (
    <section className="section" aria-labelledby="events-title">
      <div className="container">
        <div className="cluster" style={{ justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <h2 id="events-title" style={{ margin: 0 }}>{t("home.eventsTitle")}</h2>
          <Link className="more-link" to="/events">{t("home.allEvents")}</Link>
        </div>
        <div className="grid grid-3">{data.items.map((e) => <EventCard key={e.id} event={e} />)}</div>
      </div>
    </section>
  );
}

// Hidden entirely until an admin adds real, verifiable impact numbers.
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

// Hidden entirely until an admin publishes gallery photos.
function GalleryStrip() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/gallery", { params: { per_page: 6 } }), []);
  const items = data ? data.items : [];
  if (!items.length) return null;
  return (
    <section className="section" aria-labelledby="gallery-title">
      <div className="container">
        <div className="cluster" style={{ justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <h2 id="gallery-title" style={{ margin: 0 }}>{t("home.galleryTitle")}</h2>
          <Link className="more-link" to="/gallery">{t("home.galleryAll")}</Link>
        </div>
        <ul className="photo-grid photo-grid-6">
          {items.map((p) => (
            <li key={p.id}>
              <Link to="/gallery" aria-label={p.alt_text}>
                <Photo src={p.image_url} alt={p.alt_text} sizes="(min-width: 72rem) 16vw, (min-width: 48rem) 33vw, 50vw" />
              </Link>
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

// Hidden entirely until an admin publishes news.
function LatestNews() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/news", { params: { per_page: 3 } }), []);
  if (!data || !data.items.length) return null;
  return (
    <section className="section section-alt" aria-labelledby="news-title">
      <div className="container">
        <div className="cluster" style={{ justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <h2 id="news-title" style={{ margin: 0 }}>{t("home.newsTitle")}</h2>
          <Link className="more-link" to="/news">{t("home.allNews")}</Link>
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
      <FeaturedProgram />
      <WellnessDayCard />
      <Intergenerational />
      <Neighborhoods />
      <UpcomingEvents />
      <ImpactStats />
      <GalleryStrip />
      <Ctas />
      <LatestNews />
    </>
  );
}
