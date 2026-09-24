import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { adminApi } from "../api";
import { ErrorNote, Loading } from "../component/common";
import { Photo } from "../component/Photo";
import { RESOURCES } from "./resources";
import { useTitle } from "./AdminApp";
import NotFound from "../pages/NotFound";

export function useProgramOptions() {
  const [programs, setPrograms] = useState([]);
  useEffect(() => {
    adminApi.get("/admin/programs", { params: { per_page: 500, sort: "title" } })
      .then((d) => setPrograms(d.items)).catch(() => {});
  }, []);
  return programs;
}

export function ResourceList() {
  const { resource } = useParams();
  const cfg = RESOURCES[resource];
  const [params, setParams] = useSearchParams();
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [notice, setNotice] = useState("");
  const [q, setQ] = useState(params.get("q") || "");
  const needsPrograms = cfg && (cfg.filters || []).some((f) => f.type === "program");
  const programs = useProgramOptions();
  useTitle(cfg ? cfg.label : "Not found");

  const key = params.toString();
  const load = () => {
    setState((s) => ({ ...s, loading: true }));
    adminApi.get(`/admin/${resource}`, { params: Object.fromEntries(params) })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (cfg) load(); }, [resource, key]);

  if (!cfg) return <NotFound />;

  const setParam = (k, v) => {
    const next = new URLSearchParams(params);
    if (v === "" || v === undefined || v === null) next.delete(k); else next.set(k, v);
    if (k !== "page") next.delete("page");
    setParams(next);
  };

  const changeStatus = async (row, value) => {
    try {
      await adminApi.patch(`/admin/${resource}/${row.id}`, { status: value });
      setNotice(`Status for ${row.participant_first_name} ${row.participant_last_name} changed to ${value}.${value === "confirmed" ? " A confirmation email was sent." : ""}`);
      load();
    } catch (err) {
      setNotice(`Couldn't change the status: ${err.message}`);
    }
  };

  const exportCsv = () => {
    const p = {};
    (cfg.exportCsv.params || []).forEach((k) => { if (params.get(k)) p[k] = params.get(k); });
    adminApi.download(cfg.exportCsv.path, cfg.exportCsv.filename, p).catch((err) => setNotice(`Export failed: ${err.message}`));
  };

  const { data } = state;
  const page = data ? data.page : 1;

  return (
    <>
      <div className="admin-head">
        <h1>{cfg.label}</h1>
        <div className="cluster">
          {cfg.exportCsv && <button type="button" className="btn btn-outline" onClick={exportCsv}>Download spreadsheet (CSV)</button>}
          <Link className="btn" to={`/admin/${resource}/new`}>+ Add {cfg.singular}</Link>
        </div>
      </div>
      {cfg.help && <p className="admin-help">{cfg.help}</p>}
      {notice && <div className="alert alert-info" role="status"><p>{notice}</p></div>}

      <form className="filters" role="search" onSubmit={(e) => { e.preventDefault(); setParam("q", q.trim()); }}>
        {cfg.search && (
          <div className="field">
            <label htmlFor="admin-q">Search</label>
            <div className="cluster" style={{ flexWrap: "nowrap" }}>
              <input id="admin-q" type="search" placeholder={cfg.search} value={q} onChange={(e) => setQ(e.target.value)} />
              <button className="btn" type="submit">Search</button>
            </div>
          </div>
        )}
        {(cfg.filters || []).map((f) => (
          <div className="field" key={f.key}>
            <label htmlFor={`f-${f.key}`}>{f.label}</label>
            <select id={`f-${f.key}`} value={params.get(f.key) || ""} onChange={(e) => setParam(f.key, e.target.value)}>
              <option value="">All</option>
              {f.type === "program"
                ? (needsPrograms ? programs : []).map((p) => <option key={p.id} value={p.id}>{p.title}</option>)
                : f.options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
        ))}
      </form>

      {state.error && <ErrorNote error={state.error} onRetry={load} />}
      {state.loading && !data && <Loading />}
      {data && (
        <>
          <p className="muted" role="status">{data.total} {data.total === 1 ? cfg.singular : cfg.label.toLowerCase()}</p>
          {data.items.length ? (
            <div className="table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    {cfg.columns.map((c) => <th key={c.key} scope="col">{c.label || <span className="sr-only">Status</span>}</th>)}
                    <th scope="col"><span className="sr-only">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row) => (
                    <tr key={row.id}>
                      {cfg.columns.map((c) => {
                        const raw = c.get ? c.get(row) : row[c.key];
                        if (c.inlineSelect) {
                          return (
                            <td key={c.key}>
                              <label className="sr-only" htmlFor={`st-${row.id}`}>Status for {row.participant_first_name} {row.participant_last_name}</label>
                              <select id={`st-${row.id}`} className={`status-select status-${raw}`} value={raw} onChange={(e) => changeStatus(row, e.target.value)}>
                                {c.inlineSelect.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                              </select>
                            </td>
                          );
                        }
                        if (c.thumb) return <td key={c.key} className="thumb-cell"><Photo src={raw} alt="" ratio="1" sizes="5rem" /></td>;
                        return <td key={c.key} className={c.className || ""}>{c.format ? c.format(raw, row) : raw}</td>;
                      })}
                      <td><Link className="btn btn-sm btn-outline" to={`/admin/${resource}/${row.id}`}>Open<span className="sr-only"> {cfg.singular} #{row.id}</span></Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className="empty">Nothing here yet.</div>}
          {data.pages > 1 && (
            <nav className="pagination" aria-label="Pages">
              <button type="button" className="btn btn-outline" disabled={page <= 1} onClick={() => setParam("page", page - 1)}>← Previous</button>
              <span>Page {page} of {data.pages}</span>
              <button type="button" className="btn btn-outline" disabled={page >= data.pages} onClick={() => setParam("page", page + 1)}>Next →</button>
            </nav>
          )}
        </>
      )}
    </>
  );
}
