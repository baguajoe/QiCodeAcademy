import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Photo } from "./Photo";
import { formatDateRange, formatLongDate, formatMonthShort, formatTimeRange, parseLocal, parseUtc, formatMediumDate } from "../format";

const PROGRAM_PH = {
  youth: "Program photo: students working on a coding project",
  senior: "Program photo: older adults in a movement class",
  intergenerational: "Program photo: a teen and an older adult learning together",
};

// "Sample venue, Dorchester" + "Dorchester" → don't repeat the neighborhood.
export function placeText(location, neighborhood) {
  if (location && neighborhood && location.toLowerCase().includes(neighborhood.toLowerCase())) return location;
  return [location, neighborhood].filter(Boolean).join(", ");
}

export function SeatsBadge({ program }) {
  const { t } = useTranslation();
  if (!program.is_active) return <span className="badge badge-muted">{t("common.notOpen")}</span>;
  if (program.seats_left === null || program.seats_left === undefined)
    return <span className="badge badge-ok">{t("common.openEnrollment")}</span>;
  if (program.seats_left === 0) return <span className="badge badge-warn">{t("common.full")}</span>;
  return <span className="badge badge-ok">{t("common.seatsLeft", { count: program.seats_left })}</span>;
}

export function ProgramCard({ program, headingLevel = 3 }) {
  const { t } = useTranslation();
  const H = `h${headingLevel}`;
  const dates = formatDateRange(program.start_date, program.end_date);
  return (
    <article className={`card card-accent theme-${program.division}`}>
      <div className="card-media">
        <Photo
          src={program.image_url}
          alt={program.image_alt || ""}
          sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw"
          placeholder={{ division: program.division, subject: PROGRAM_PH[program.division] || "Program photo", size: "1200×750" }}
        />
      </div>
      <div className="card-body">
        <div className="cluster" style={{ gap: "0.5rem" }}>
          <span className="badge">{t(`divisions.${program.division}.short`)}</span>
          <SeatsBadge program={program} />
        </div>
        <H>{program.title}</H>
        {program.description && <p>{program.description}</p>}
        <ul className="meta-list">
          {program.age_range && <li><strong>{t("common.ages")}</strong> {program.age_range}</li>}
          {program.schedule && <li><strong>{t("common.schedule")}</strong> {program.schedule}</li>}
          {dates && <li><strong>{t("common.dates")}</strong> {dates}</li>}
          {(program.location || program.neighborhood) && (
            <li><strong>{t("common.location")}</strong> {placeText(program.location, program.neighborhood)}</li>
          )}
          {program.cost && <li><strong>{t("common.cost")}</strong> {program.cost}</li>}
        </ul>
      </div>
      <div className="card-footer">
        {program.is_active ? (
          <Link className="btn" to={`/register/${program.slug}`}>
            {t("common.register")}<span className="sr-only">: {program.title}</span>
          </Link>
        ) : (
          <span className="muted">{t("register.closed")}</span>
        )}
      </div>
    </article>
  );
}

export function EventCard({ event, headingLevel = 3 }) {
  const { t } = useTranslation();
  const H = `h${headingLevel}`;
  const start = parseLocal(event.start_datetime);
  const end = parseLocal(event.end_datetime);
  return (
    <article className={`card event-card theme-${event.division}`}>
      <div className="event-card-inner">
        <div className="date-block" aria-hidden="true">
          <span className="m">{formatMonthShort(start)}</span>
          <span className="d">{start.getDate()}</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <span className="badge">{t(`divisions.${event.division}.short`)}</span>
          <H><Link to={`/events/${event.slug}`}>{event.title}</Link></H>
          <p className="muted" style={{ margin: 0 }}>
            <time dateTime={event.start_datetime}>{formatLongDate(start)}</time>
            <br />
            {formatTimeRange(start, end)}
          </p>
          {(event.location || event.neighborhood) && (
            <p className="muted" style={{ margin: 0 }}>{placeText(event.location, event.neighborhood)}</p>
          )}
        </div>
      </div>
    </article>
  );
}

export function NewsCard({ post, headingLevel = 3 }) {
  const { t } = useTranslation();
  const H = `h${headingLevel}`;
  const theme = { seniors: "senior", youth: "youth", research: "research" }[post.category] || "community";
  return (
    <article className={`card theme-${theme}`}>
      <div className="card-media">
        <Photo src={post.cover_image_url} alt={post.cover_image_alt || ""}
          sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw"
          placeholder={{ division: theme, subject: "News cover photo", size: "1200×750" }} />
      </div>
      <div className="card-body">
        <span className="badge">{t(`news.categories.${post.category}`)}</span>
        <H><Link to={`/news/${post.slug}`}>{post.title}</Link></H>
        <p className="muted small" style={{ margin: 0 }}>
          <time dateTime={post.published_at}>{formatMediumDate(parseUtc(post.published_at))}</time>
        </p>
        {post.excerpt && <p>{post.excerpt}</p>}
      </div>
    </article>
  );
}
