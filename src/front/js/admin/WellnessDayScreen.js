// Senior Wellness Day overview: interest-list totals and breakdowns, partner status counts,
// and the confirmed lineup (API: /api/admin/wellness-day/summary).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../api";
import { ErrorNote, Loading } from "../component/common";
import { useTitle } from "./AdminApp";
import { WD_ACTIVITIES, WD_STATUS, WD_TYPES } from "./resources";

const label = (opts, v) => (opts.find((o) => o[0] === v) || [v, v])[1];

function CountTable({ caption, rows }) {
  return (
    <div className="table-wrap">
      <table className="admin-table">
        <caption className="sr-only">{caption}</caption>
        <tbody>
          {rows.map(([name, n, to]) => (
            <tr key={name}>
              <th scope="row">{to ? <Link to={to}>{name}</Link> : name}</th>
              <td>{n}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function WellnessDayScreen() {
  useTitle("Senior Wellness Day");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const load = () => adminApi.get("/admin/wellness-day/summary").then(setData).catch(setError);
  useEffect(() => { load(); }, []);

  if (error) return <ErrorNote error={error} onRetry={load} />;
  if (!data) return <Loading />;

  const hoods = Object.entries(data.interest_by_neighborhood).map(([k, n]) =>
    [k === "not_given" ? "Not given" : k, n, k === "not_given" ? null : `/admin/wellness-day-interest?neighborhood=${encodeURIComponent(k)}`]);
  return (
    <>
      <div className="admin-head">
        <h1>Senior Wellness Day</h1>
        <div className="cluster">
          <Link className="btn btn-outline" to="/admin/settings">Edit date, location &amp; badge</Link>
          <a className="btn btn-outline" href="/programs/seniors/wellness-day" target="_blank" rel="noopener noreferrer">View page ↗</a>
        </div>
      </div>
      <ul className="admin-tiles">
        <li><Link to="/admin/wellness-day-interest"><span className="value">{data.interest_total}</span><span className="label">Interest list sign-ups</span></Link></li>
        {WD_STATUS.map(([k, l]) => (
          <li key={k}><Link to={`/admin/wellness-day-partners?status=${k}`}><span className="value">{data.partners_by_status[k]}</span><span className="label">Partners: {l}</span></Link></li>
        ))}
      </ul>

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <section aria-labelledby="wd-act">
          <h2 id="wd-act">Interest by activity</h2>
          <CountTable caption="Interest by activity" rows={WD_ACTIVITIES.map(([k, l]) =>
            [l, data.interest_by_activity[k], `/admin/wellness-day-interest?activity=${k}`])} />
        </section>
        <section aria-labelledby="wd-hood">
          <h2 id="wd-hood">Interest by neighborhood</h2>
          <CountTable caption="Interest by neighborhood" rows={hoods} />
        </section>
      </div>

      <section aria-labelledby="wd-types">
        <h2 id="wd-types">Partner submissions by type</h2>
        <CountTable caption="Partner submissions by type" rows={WD_TYPES.map(([k, l]) =>
          [l, data.partners_by_type[k], `/admin/wellness-day-partners?participation_type=${k}`])} />
      </section>

      <section aria-labelledby="wd-lineup">
        <h2 id="wd-lineup">Confirmed lineup</h2>
        <p className="admin-help">Everyone with status Confirmed. Only rows marked "Public" appear in "Who's joining us" on the website (organization or name + type only).</p>
        {data.confirmed_lineup.length ? (
          <div className="table-wrap">
            <table className="admin-table">
              <thead><tr><th scope="col">Organization / name</th><th scope="col">Participating as</th><th scope="col">Contact</th><th scope="col">License</th><th scope="col">Public?</th></tr></thead>
              <tbody>
                {data.confirmed_lineup.map((p) => (
                  <tr key={p.id}>
                    <th scope="row"><Link to={`/admin/wellness-day-partners/${p.id}`}>{p.display_name}</Link></th>
                    <td>{(p.participation_types || []).map((t) => label(WD_TYPES, t)).join(", ")}</td>
                    <td>{[p.email, p.phone].filter(Boolean).join(" · ")}</td>
                    <td>{[p.license_type, p.license_number].filter(Boolean).join(" ") || "—"}</td>
                    <td>{p.show_publicly ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <div className="empty">No confirmed partners yet.</div>}
      </section>
    </>
  );
}
