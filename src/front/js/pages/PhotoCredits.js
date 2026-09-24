// Photo credits: default site photos (credits.json) + any admin-uploaded site photos with a credit.
import { useTranslation } from "react-i18next";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { PageBanner } from "../component/common";
import { ALL_CREDITS, SLOTS } from "../siteImages";

export default function PhotoCredits() {
  const { t } = useTranslation();
  const { store } = useStore();
  useSeo({ title: t("credits.title"), description: t("credits.lead") });
  const uploads = store.siteImages || {};
  const rows = Object.keys(SLOTS).map((slot) => {
    const up = uploads[slot];
    if (up && up.image_url) {
      return up.credit ? { slot, credit: up.credit, type: up.is_stock ? "stock" : "own", license: null, url: null } : null;
    }
    const c = ALL_CREDITS[slot];
    return c ? { slot, credit: c.credit, type: c.type === "stock" ? "stock" : "own", license: c.license, url: c.page_url } : null;
  }).filter(Boolean);

  return (
    <div className="theme-community">
      <PageBanner title={t("credits.title")} lead={t("credits.lead")} />
      <section className="section">
        <div className="container">
          {rows.length ? (
            <div className="table-wrap">
              <table className="credits-table">
                <thead>
                  <tr><th scope="col">{t("credits.where")}</th><th scope="col">{t("credits.credit")}</th><th scope="col">{t("credits.type")}</th><th scope="col">{t("credits.license")}</th></tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.slot}>
                      <th scope="row">{SLOTS[r.slot].page}</th>
                      <td>{r.url ? <a href={r.url} target="_blank" rel="noopener noreferrer">{r.credit}<span className="sr-only"> ({t("common.opensNewTab")})</span></a> : r.credit}</td>
                      <td>{r.type === "stock" ? t("credits.stock") : t("credits.own")}</td>
                      <td>{r.license || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">{t("credits.none")}</p>}
          <p className="muted" style={{ marginTop: "1.5rem" }}>{t("credits.note")}</p>
        </div>
      </section>
    </div>
  );
}
