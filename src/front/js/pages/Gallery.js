import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useSeo } from "../seo";
import { Empty, ErrorNote, Loading, PageBanner } from "../component/common";
import { Photo } from "../component/Photo";

const DIVISIONS = ["youth", "senior", "intergenerational", "research", "community"];

// Accessible lightbox on the native <dialog>: focus is trapped, Esc closes,
// arrow keys move between photos, and focus returns to the opening thumbnail.
function Lightbox({ photos, index, onClose, onIndex, returnFocus }) {
  const { t } = useTranslation();
  const ref = useRef(null);
  const open = index !== null;

  useEffect(() => {
    const dlg = ref.current;
    if (!dlg) return;
    if (open && !dlg.open) dlg.showModal();
    if (!open && dlg.open) dlg.close();
  }, [open]);

  useEffect(() => {
    const dlg = ref.current;
    const onKey = (e) => {
      if (!open) return;
      if (e.key === "ArrowRight") onIndex((index + 1) % photos.length);
      if (e.key === "ArrowLeft") onIndex((index - 1 + photos.length) % photos.length);
    };
    const onCloseEvt = () => {
      onClose();
      if (returnFocus.current) returnFocus.current.focus();
    };
    dlg.addEventListener("keydown", onKey);
    dlg.addEventListener("close", onCloseEvt);
    return () => {
      dlg.removeEventListener("keydown", onKey);
      dlg.removeEventListener("close", onCloseEvt);
    };
  }, [open, index, photos.length, onClose, onIndex, returnFocus]);

  const photo = open ? photos[index] : null;
  return (
    <dialog ref={ref} className="lightbox" aria-labelledby="lightbox-caption"
      onClick={(e) => { if (e.target === ref.current) ref.current.close(); }}>
      {photo && (
        <div className="lightbox-inner">
          <div className="lightbox-bar">
            <p className="lightbox-count" aria-live="polite">{t("gallery.counter", { index: index + 1, total: photos.length })}</p>
            <button type="button" className="btn btn-light" onClick={() => ref.current.close()} autoFocus>
              ✕ {t("common.close")}
            </button>
          </div>
          <figure>
            <Photo src={photo.image_url} alt={photo.alt_text} sizes="100vw" fit="contain" className="lightbox-photo" priority />
            <figcaption id="lightbox-caption">{photo.caption || photo.alt_text}</figcaption>
          </figure>
          {photos.length > 1 && (
            <div className="lightbox-nav">
              <button type="button" className="btn btn-light" onClick={() => onIndex((index - 1 + photos.length) % photos.length)}>← {t("gallery.prev")}</button>
              <button type="button" className="btn btn-light" onClick={() => onIndex((index + 1) % photos.length)}>{t("gallery.next")} →</button>
            </div>
          )}
        </div>
      )}
    </dialog>
  );
}

export default function Gallery() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const division = params.get("division") || "";
  const [state, setState] = useState({ items: [], page: 0, pages: 1, loading: true, error: null });
  const [index, setIndex] = useState(null);
  const opener = useRef(null);
  useSeo({ title: t("gallery.title"), description: t("gallery.lead") });

  const load = (page, reset) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    api.get("/gallery", { params: { division, page, per_page: 24 } })
      .then((d) => setState((s) => ({ items: reset ? d.items : [...s.items, ...d.items], page: d.page, pages: d.pages, loading: false, error: null })))
      .catch((error) => setState((s) => ({ ...s, loading: false, error })));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => load(1, true), [division]);

  return (
    <div className="theme-community">
      <PageBanner title={t("gallery.title")} lead={t("gallery.lead")} />
      <section className="section">
        <div className="container">
          <div className="filters" role="group" aria-labelledby="gal-filter-label">
            <span id="gal-filter-label" style={{ fontWeight: 700 }}>{t("gallery.filter")}</span>
            <div className="cluster">
              {["", ...DIVISIONS].map((d) => (
                <button key={d || "all"} type="button" className={`btn btn-sm ${division === d ? "" : "btn-outline"}`}
                  aria-pressed={division === d} onClick={() => setParams(d ? { division: d } : {})}>
                  {d ? t(`divisions.${d}.short`) : t("gallery.all")}
                </button>
              ))}
            </div>
          </div>
          {state.error && <ErrorNote error={state.error} onRetry={() => load(1, true)} />}
          {state.items.length ? (
            <ul className="photo-grid photo-grid-4">
              {state.items.map((p, i) => (
                <li key={p.id}>
                  <figure style={{ margin: 0 }}>
                    <button type="button" aria-label={t("gallery.open", { alt: p.alt_text })}
                      onClick={(e) => { opener.current = e.currentTarget; setIndex(i); }}>
                      <Photo src={p.image_url} alt="" sizes="(min-width: 72rem) 25vw, (min-width: 48rem) 33vw, 50vw" />
                    </button>
                    {p.caption && <figcaption>{p.caption}</figcaption>}
                  </figure>
                </li>
              ))}
            </ul>
          ) : state.loading ? <Loading /> : <Empty>{t("gallery.empty")}</Empty>}
          {state.page < state.pages && (
            <div className="pagination">
              <button type="button" className="btn btn-outline" disabled={state.loading} onClick={() => load(state.page + 1)}>
                {t("gallery.loadMore")}
              </button>
            </div>
          )}
        </div>
      </section>
      <Lightbox photos={state.items} index={index} onIndex={setIndex} onClose={() => setIndex(null)} returnFocus={opener} />
    </div>
  );
}
