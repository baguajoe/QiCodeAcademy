import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { ProgramCard } from "./Cards";
import { Empty, ErrorNote, Loading } from "./common";

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
