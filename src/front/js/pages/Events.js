import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { Empty, ErrorNote, Loading, PageBanner } from "../component/common";
import { EventCard, placeText } from "../component/Cards";
import { Photo } from "../component/Photo";
import { Paragraphs } from "../component/Founder";
import NotFound from "./NotFound";
import { formatLongDate, formatMonthYear, formatTime, formatTimeRange, formatWeekdayShort, isoDate, parseLocal } from "../format";

const DIVISIONS = ["youth", "senior", "intergenerational", "research", "community"];

function Filters({ params, setParam }) {
  const { t } = useTranslation();
  const hoods = t("neighborhoods.list", { returnObjects: true });
  const view = params.get("view") || "list";
  return (
    <div className="filters" role="group" aria-label={t("events.filters")}>
      <div className="field">
        <span className="label" id="view-label">{t("events.view")}</span>
        <div className="segmented" role="group" aria-labelledby="view-label">
          <button type="button" aria-pressed={view === "list"} onClick={() => setParam("view", "list")}>{t("events.listView")}</button>
          <button type="button" aria-pressed={view === "calendar"} onClick={() => setParam("view", "calendar")}>{t("events.calendarView")}</button>
        </div>
      </div>
      {view === "list" && (
        <div className="field">
          <label htmlFor="ev-when">{t("events.when")}</label>
          <select id="ev-when" value={params.get("when") || "upcoming"} onChange={(e) => setParam("when", e.target.value)}>
            <option value="upcoming">{t("events.upcoming")}</option>
            <option value="past">{t("events.past")}</option>
          </select>
        </div>
      )}
      <div className="field">
        <label htmlFor="ev-division">{t("events.division")}</label>
        <select id="ev-division" value={params.get("division") || ""} onChange={(e) => setParam("division", e.target.value)}>
          <option value="">{t("events.allDivisions")}</option>
          {DIVISIONS.map((d) => <option key={d} value={d}>{t(`divisions.${d}.short`)}</option>)}
        </select>
      </div>
      <div className="field">
        <label htmlFor="ev-hood">{t("events.neighborhood")}</label>
        <select id="ev-hood" value={params.get("neighborhood") || ""} onChange={(e) => setParam("neighborhood", e.target.value)}>
          <option value="">{t("events.allNeighborhoods")}</option>
          {hoods.map((h) => <option key={h} value={h}>{h}</option>)}
        </select>
      </div>
    </div>
  );
}

function EventList({ filters }) {
  const { t } = useTranslation();
  const [pages, setPages] = useState({ items: [], page: 0, pages: 1, loading: true, error: null });
  const key = JSON.stringify(filters);

  const load = (page, reset) => {
    setPages((s) => ({ ...s, loading: true, error: null }));
    api.get("/events", { params: { ...filters, page, per_page: 12 } })
      .then((d) => setPages((s) => ({ items: reset ? d.items : [...s.items, ...d.items], page: d.page, pages: d.pages, loading: false, error: null })))
      .catch((error) => setPages((s) => ({ ...s, loading: false, error })));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => load(1, true), [key]);

  if (pages.error) return <ErrorNote error={pages.error} onRetry={() => load(1, true)} />;
  return (
    <>
      <p className="sr-only" role="status" aria-live="polite">{pages.loading ? t("common.loading") : t("events.count", { count: pages.items.length })}</p>
      {pages.items.length ? (
        <div className="grid grid-3">{pages.items.map((e) => <EventCard key={e.id} event={e} headingLevel={2} />)}</div>
      ) : pages.loading ? <Loading /> : <Empty>{t("events.noEvents")}</Empty>}
      {pages.page < pages.pages && (
        <div className="pagination">
          <button type="button" className="btn btn-outline" disabled={pages.loading} onClick={() => load(pages.page + 1)}>
            {pages.loading ? t("common.loading") : t("events.loadMore")}
          </button>
        </div>
      )}
    </>
  );
}

function monthMatrix(year, month) {
  const first = new Date(year, month, 1);
  const start = new Date(year, month, 1 - first.getDay()); // weeks start Sunday
  const weeks = [];
  for (let w = 0; w < 6; w++) {
    const days = [];
    for (let d = 0; d < 7; d++) days.push(new Date(start.getFullYear(), start.getMonth(), start.getDate() + w * 7 + d));
    if (w >= 4 && days[0].getMonth() !== month) break;
    weeks.push(days);
  }
  return weeks;
}

function Calendar({ filters, params, setParam }) {
  const { t } = useTranslation();
  const today = new Date();
  const monthParam = params.get("month"); // YYYY-MM
  const [y, m] = monthParam && /^\d{4}-\d{2}$/.test(monthParam)
    ? monthParam.split("-").map(Number) : [today.getFullYear(), today.getMonth() + 1];
  const first = new Date(y, m - 1, 1);
  const last = new Date(y, m, 0);
  const { data, error, loading, reload } = useApi(
    () => api.get("/events", { params: { ...filters, when: "all", start: isoDate(first), end: isoDate(last), per_page: 200 } }),
    [y, m, JSON.stringify(filters)]
  );
  const byDay = useMemo(() => {
    const map = {};
    (data ? data.items : []).forEach((e) => {
      const k = e.start_datetime.slice(0, 10);
      (map[k] = map[k] || []).push(e);
    });
    Object.values(map).forEach((list) => list.sort((a, b) => a.start_datetime.localeCompare(b.start_datetime)));
    return map;
  }, [data]);
  const go = (delta) => {
    const d = new Date(y, m - 1 + delta, 1);
    setParam("month", `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };
  const weeks = monthMatrix(y, m - 1);
  const monthLabel = formatMonthYear(first);
  const daysWithEvents = Object.keys(byDay).sort();

  return (
    <div className="calendar">
      <div className="cal-nav">
        <button type="button" className="btn btn-outline btn-sm" onClick={() => go(-1)}>← {t("events.prevMonth")}</button>
        <h2 aria-live="polite" style={{ margin: 0 }}>{monthLabel}</h2>
        <button type="button" className="btn btn-outline btn-sm" onClick={() => go(1)}>{t("events.nextMonth")} →</button>
      </div>
      <p className="center"><button type="button" className="link-button" onClick={() => setParam("month", "")}>{t("events.thisMonth")}</button></p>
      {error && <ErrorNote error={error} onRetry={reload} />}
      {loading && <Loading />}

      {/* Month grid (tablets and larger) */}
      <div className="cal-grid-wrap">
        <table className="cal-grid">
          <caption className="sr-only">{monthLabel}</caption>
          <thead>
            <tr>{weeks[0].map((d) => <th key={d.getDay()} scope="col">{formatWeekdayShort(d)}</th>)}</tr>
          </thead>
          <tbody>
            {weeks.map((week, i) => (
              <tr key={i}>
                {week.map((d) => {
                  const k = isoDate(d);
                  const events = byDay[k] || [];
                  const outside = d.getMonth() !== m - 1;
                  const isToday = k === isoDate(today);
                  return (
                    <td key={k} className={`${outside ? "outside" : ""} ${isToday ? "today" : ""}`}>
                      <span className="day-num" aria-hidden={events.length ? undefined : "true"}>
                        {d.getDate()}{isToday && <span className="sr-only"> ({t("events.today")})</span>}
                      </span>
                      {events.length > 0 && (
                        <ul aria-label={t("events.moreOnDay", { date: formatLongDate(d) })}>
                          {events.map((e) => (
                            <li key={e.id} className={`theme-${e.division}`}>
                              <Link to={`/events/${e.slug}`}>
                                <span className="cal-time">{formatTime(parseLocal(e.start_datetime))}</span> {e.title}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Agenda (phones) */}
      <div className="cal-agenda">
        {!loading && !daysWithEvents.length && <Empty>{t("events.noEvents")}</Empty>}
        {daysWithEvents.map((k) => (
          <section key={k} aria-label={formatLongDate(parseLocal(k))}>
            <h3>{formatLongDate(parseLocal(k))}</h3>
            <ul>
              {byDay[k].map((e) => (
                <li key={e.id}>
                  <Link to={`/events/${e.slug}`}>{e.title}</Link>
                  <span className="muted"> — {formatTimeRange(parseLocal(e.start_datetime), parseLocal(e.end_datetime))}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}

export default function Events() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  useSeo({ title: t("events.title"), description: t("events.lead"), imageSlot: "events-banner" });
  const setParam = (k, v) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v);
    else next.delete(k);
    setParams(next, { replace: true });
  };
  const filters = {
    division: params.get("division") || undefined,
    neighborhood: params.get("neighborhood") || undefined,
  };
  const view = params.get("view") || "list";
  return (
    <div className="theme-community">
      <PageBanner slot="events-banner" title={t("events.title")} lead={t("events.lead")} />
      <section className="section">
        <div className="container">
          <Filters params={params} setParam={setParam} />
          {view === "calendar"
            ? <Calendar filters={filters} params={params} setParam={setParam} />
            : <EventList filters={{ ...filters, when: params.get("when") || "upcoming" }} />}
        </div>
      </section>
    </div>
  );
}

// NY UTC offset for a wall-clock date, e.g. "-04:00" (for schema.org Event dates).
function nyOffset(date) {
  try {
    const part = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", timeZoneName: "shortOffset" })
      .formatToParts(date).find((p) => p.type === "timeZoneName").value; // "GMT-4"
    const m = part.match(/GMT([+-]\d+)(?::(\d+))?/);
    if (!m) return "-05:00";
    const h = Number(m[1]);
    return `${h < 0 ? "-" : "+"}${String(Math.abs(h)).padStart(2, "0")}:${m[2] || "00"}`;
  } catch {
    return "-05:00";
  }
}

export function EventDetail() {
  const { t } = useTranslation();
  const { slug } = useParams();
  const { data: ev, error, loading, reload } = useApi(() => api.get(`/events/${slug}`), [slug]);
  const start = ev ? parseLocal(ev.start_datetime) : null;
  const end = ev ? parseLocal(ev.end_datetime) : null;
  const place = ev ? placeText(ev.location, ev.neighborhood) : "";
  useSeo(ev ? {
    title: ev.title,
    description: `${formatLongDate(start)}, ${formatTimeRange(start, end)}${place ? ` — ${place}` : ""}. ${ev.description || ""}`.slice(0, 300),
    image: ev.image_url || undefined,
    imageSlot: "events-banner",
    jsonLd: [{
      "@context": "https://schema.org",
      "@type": "Event",
      name: ev.title,
      description: ev.description,
      startDate: `${ev.start_datetime}:00${nyOffset(start)}`,
      ...(ev.end_datetime ? { endDate: `${ev.end_datetime}:00${nyOffset(end)}` } : {}),
      eventStatus: "https://schema.org/EventScheduled",
      eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
      location: { "@type": "Place", name: ev.location || ev.neighborhood || "Boston",
        address: { "@type": "PostalAddress", addressLocality: ev.neighborhood ? `${ev.neighborhood}, Boston` : "Boston", addressRegion: "MA", addressCountry: "US" } },
      organizer: { "@type": "NGO", name: "Qi Code Academy", url: window.location.origin },
      url: window.location.href,
      ...(ev.image_url ? { image: [ev.image_url.startsWith("http") ? ev.image_url : window.location.origin + ev.image_url] } : {}),
    }],
  } : { title: t("events.title") });

  if (loading) return <div className="container section"><Loading /></div>;
  if (error && error.status === 404) return <NotFound />;
  if (error) return <div className="container section"><ErrorNote error={error} onRetry={reload} /></div>;

  return (
    <article className={`theme-${ev.division}`}>
      <section className="banner banner-plain">
        <div className="container banner-content">
          <nav className="breadcrumb" aria-label={t("common.breadcrumb")}><Link to="/events">← {t("events.back")}</Link></nav>
          <span className="badge badge-solid" style={{ alignSelf: "flex-start", marginBottom: "0.75rem" }}>{t(`divisions.${ev.division}.short`)}</span>
          <h1>{ev.title}</h1>
        </div>
      </section>
      <section className="section">
        <div className="container split split-wide-left" style={{ alignItems: "start" }}>
          <div className="prose">
            {ev.image_url && <Photo src={ev.image_url} alt={ev.image_alt || ""} ratio="16 / 9" sizes="(min-width: 56rem) 40rem, 100vw" priority />}
            <Paragraphs text={ev.description} />
          </div>
          <aside className="gain">
            <dl className="event-facts">
              <dt>{t("events.date")}</dt>
              <dd><time dateTime={ev.start_datetime}>{formatLongDate(start)}</time></dd>
              <dt>{t("events.time")}</dt>
              <dd>{formatTimeRange(start, end)}</dd>
              {place && (<><dt>{t("events.where")}</dt><dd>{place}</dd></>)}
            </dl>
            <a className="btn btn-block" href={`/api/events/${ev.slug}/ics`} download={`${ev.slug}.ics`}>
              {t("events.addToCalendar")}
            </a>
          </aside>
        </div>
      </section>
    </article>
  );
}
