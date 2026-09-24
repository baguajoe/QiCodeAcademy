import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { ProgramCard } from "./Cards";
import { Empty, ErrorNote, Loading } from "./common";

// A whole "open programs" section that only appears when there are programs to show.
export function ProgramSection({ division, title, lead, id }) {
  const { data } = useApi(() => api.get("/programs", { params: { division } }), [division]);
  if (!data || !data.items.length) return null;
  return (
    <section className="section" aria-labelledby={id}>
      <div className="container">
        <div className="section-header">
          <h2 id={id}>{title}</h2>
          {lead && <p className="lead">{lead}</p>}
        </div>
        <div className="grid grid-3">{data.items.map((p) => <ProgramCard key={p.id} program={p} />)}</div>
      </div>
    </section>
  );
}

// Active programs for one division, as cards with Register buttons.
export function ProgramList({ division, emptyText }) {
  const { t } = useTranslation();
  const { data, error, loading, reload } = useApi(() => api.get("/programs", { params: { division } }), [division]);
  if (loading) return <Loading />;
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!data.items.length) return <Empty>{emptyText || t("common.comingSoon")}</Empty>;
  return (
    <div className="grid grid-3">
      {data.items.map((p) => <ProgramCard key={p.id} program={p} />)}
    </div>
  );
}
