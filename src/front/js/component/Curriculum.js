// Curriculum modules from GET /api/curriculum. Empty fields are never rendered.
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { OptionalSiteImage } from "./Photo";

export function useCurriculum(division) {
  const { data, loading } = useApi(() => api.get("/curriculum", { params: { division } }), [division]);
  return { modules: data ? data.items : [], loading };
}

export function StatusBadge({ module }) {
  const { t } = useTranslation();
  if (module.status === "in_development") {
    return <span className="badge badge-solid">{module.launch_label || t("common.inDevelopment")}</span>;
  }
  return module.launch_label ? <span className="badge">{module.launch_label}</span> : null;
}

function List({ title, items, ordered, className = "" }) {
  if (!items || !items.length) return null;
  const L = ordered ? "ol" : "ul";
  return (
    <>
      <h4 className="module-subhead">{title}</h4>
      <L className={`module-list ${className}`}>{items.map((i) => <li key={i}>{i}</li>)}</L>
    </>
  );
}

export function ModuleCard({ module, headingLevel = 3, showProjects = true, photoSlot }) {
  const { t } = useTranslation();
  const H = `h${headingLevel}`;
  // Labels for learning_goals / projects depend on the division.
  const labels = t(`curriculum.${module.division}`, { returnObjects: true });
  const facts = [module.age_range, module.duration, ...(module.format_notes || [])].filter(Boolean);
  return (
    <article className={`card card-accent module-card theme-${module.division}`}>
      {photoSlot && <OptionalSiteImage slot={photoSlot} className="module-photo" sizes="(min-width: 40rem) 50vw, 100vw" />}
      <div className="card-body">
        <div className="cluster" style={{ gap: "0.5rem" }}><StatusBadge module={module} /></div>
        <H>{module.title}</H>
        {facts.length > 0 && <ul className="fact-chips">{facts.map((f) => <li key={f}>{f}</li>)}</ul>}
        {module.summary && <p>{module.summary}</p>}
        <List title={labels.goals} items={module.learning_goals} />
        {showProjects && <List title={labels.projects} items={module.projects} ordered className="progression" />}
        {module.adaptations && (
          <>
            <h4 className="module-subhead">{labels.adaptations}</h4>
            <p>{module.adaptations}</p>
          </>
        )}
      </div>
    </article>
  );
}

// "Project — what it teaches" lines as a week-by-week timeline.
export function WeeklyProjects({ projects, weekLabel }) {
  if (!projects || !projects.length) return null;
  return (
    <ol className="week-list">
      {projects.map((p, i) => {
        const [name, ...rest] = p.split(" — ");
        return (
          <li key={p}>
            <span className="week-n">{weekLabel(i + 1)}</span>
            <span className="week-body">
              <strong>{name}</strong>
              {rest.length > 0 && <span className="muted"> — {rest.join(" — ")}</span>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

// Time → activity schedule (e.g. a 90-minute youth session or a one-hour senior class).
export function ScheduleTable({ caption, rows }) {
  const { t } = useTranslation();
  return (
    <div className="table-wrap schedule">
      <table>
        <caption className="sr-only">{caption}</caption>
        <thead><tr><th scope="col">{t("curriculum.time")}</th><th scope="col">{t("curriculum.activity")}</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.time + r.activity}><th scope="row">{r.time}</th><td>{r.activity}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// `photos` maps an item index to a photo slot shown inside that feature card.
// `photos` maps an item index to a photo slot shown inside that feature card.
export function FeatureGrid({ items, photos = {} }) {
  return (
    <ul className="feature-grid">
      {items.map((f, i) => (
        <li key={f.title} className={`feature ${photos[i] ? "feature-with-photo" : ""}`}>
          {photos[i] && <OptionalSiteImage slot={photos[i]} className="feature-photo" sizes="(min-width: 64rem) 40vw, 100vw" />}
          <div>
            <h3>{f.title}</h3>
            <p>{f.body}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
