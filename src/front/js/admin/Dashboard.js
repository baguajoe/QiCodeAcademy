import { Link } from "react-router-dom";
import { Loading } from "../component/common";
import { useTitle } from "./AdminApp";

const money = (c) => `$${((c || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const DESIGNATION = { general: "Where needed most", youth: "Youth", senior: "Seniors", research: "Research" };

export function Dashboard({ data }) {
  useTitle("Dashboard");
  if (!data || !data.registrations_by_program) return <Loading />;
  const d = data.donations;
  const tiles = [
    { label: "Pending registrations", value: data.registrations_pending, to: "/admin/registrations?status=pending" },
    { label: "On waitlists", value: data.registrations_waitlist, to: "/admin/registrations?status=waitlist" },
    { label: "Unread messages", value: data.unread_messages, to: "/admin/contact-messages?is_read=false" },
    { label: "New research inquiries", value: data.new_research_inquiries, to: "/admin/research-inquiries?is_read=false" },
    { label: "New volunteers (30 days)", value: data.volunteers_last_30_days, to: "/admin/volunteers" },
    { label: "Research interest sign-ups", value: data.research_interest_total, to: "/admin/research-interest" },
  ];
  return (
    <>
      <h1>Dashboard</h1>
      <ul className="admin-tiles">
        {tiles.map((t) => (
          <li key={t.label}>
            <Link to={t.to}><span className="value">{t.value}</span><span className="label">{t.label}</span></Link>
          </li>
        ))}
      </ul>

      <section aria-labelledby="dash-reg">
        <h2 id="dash-reg">Registrations by program</h2>
        <div className="table-wrap">
          <table className="admin-table">
            <thead>
              <tr><th scope="col">Program</th><th scope="col">Pending</th><th scope="col">Confirmed</th><th scope="col">Waitlist</th><th scope="col">Cancelled</th><th scope="col">Seats left</th></tr>
            </thead>
            <tbody>
              {data.registrations_by_program.map((p) => (
                <tr key={p.program_id}>
                  <th scope="row"><Link to={`/admin/registrations?program_id=${p.program_id}`}>{p.title}</Link>{!p.is_active && <span className="badge badge-muted"> closed</span>}</th>
                  <td>{p.pending}</td><td>{p.confirmed}</td><td>{p.waitlist}</td><td>{p.cancelled}</td>
                  <td>{p.seats_left === null ? "Unlimited" : p.seats_left}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="dash-don">
        <h2 id="dash-don">Donations</h2>
        <p className="lead">Total received: <strong>{money(d.total_amount_cents)}</strong> · Last 30 days: <strong>{money(d.last_30_days_amount_cents)}</strong> · Active monthly donors: <strong>{d.active_monthly_donors}</strong></p>
        <ul className="admin-tiles small-tiles">
          {Object.entries(d.totals_by_designation).map(([k, v]) => (
            <li key={k}><div><span className="value">{money(v.amount_cents)}</span><span className="label">{DESIGNATION[k]} · {v.count} gifts</span></div></li>
          ))}
        </ul>
        <h3>Recent donations</h3>
        {d.recent.length ? (
          <div className="table-wrap">
            <table className="admin-table">
              <thead><tr><th scope="col">Date</th><th scope="col">Donor</th><th scope="col">Amount</th><th scope="col">Monthly?</th><th scope="col">Designation</th></tr></thead>
              <tbody>
                {d.recent.map((r) => (
                  <tr key={r.id}>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                    <td><Link to={`/admin/donations/${r.id}`}>{r.donor_name || r.donor_email || "Anonymous"}</Link></td>
                    <td>{money(r.amount_cents)}</td><td>{r.recurring ? "Yes" : "No"}</td><td>{DESIGNATION[r.designation]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="muted">No completed donations yet.</p>}
      </section>
    </>
  );
}
