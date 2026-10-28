import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../api";
import { ErrorNote, Loading } from "../component/common";
import { useStore } from "../store/appContext";
import { useTitle } from "./AdminApp";

// Friendly editor for the site settings the website reads (API: /api/admin/settings).
const GROUPS = [
  {
    title: "Organization",
    items: [
      { key: "tax_status", label: "Tax-exempt status statement", type: "textarea", rows: 3,
        hint: "Shown on the About page (Nonprofit status) and the Donate pages, and in donation receipts. Keep it matching the IRS determination letter." },
      { key: "ein", label: "EIN (federal tax ID)", hint: "Shown in the footer on every page, e.g. 42-5318171." },
      { key: "org_history", label: "Our history", type: "textarea", rows: 5,
        hint: "Shown near the top of the About page. The organization was incorporated in 2026; \"18 years\" refers to Joseph's teaching, never the organization's age. Leave blank to use the default text." },
      { key: "org_contact_email", label: "Organization email", type: "email", hint: "Shown on the Contact page and footer. Leave blank to hide. Never use a personal address." },
      { key: "org_contact_phone", label: "Organization phone", type: "tel", hint: "Shown on the Contact page and footer. Leave blank to hide. Never use a personal number." },
      { key: "teaching_locations", label: "Where we teach", type: "textarea", rows: 4,
        hint: "Shown on the Contact page. One place per line, names only (e.g. \"Codman Square Library\"). Do not add street addresses." },
    ],
  },
  {
    title: "Donations",
    note: "Keep online donations off until the Massachusetts Attorney General charity registration is complete.",
    items: [
      { key: "donations_enabled", label: "Online donations", type: "select",
        options: [["false", "Off: Donate page shows the notice below"], ["true", "On: Donate page shows the Stripe donation form"]],
        hint: "Turning this on also needs the Stripe keys set on the server." },
      { key: "donations_notice", label: "Donate page notice (while donations are off)", type: "textarea", rows: 3,
        hint: "Leave blank to use the default text." },
    ],
  },
  {
    title: "Home page: featured program",
    note: "The band below the three division cards. Describe what happens in class and what we plan to study. Never promise health outcomes.",
    items: [
      { key: "featured_program_title", label: "Featured program title", hint: "e.g. \"Baguazhang for Healthy Aging\"" },
      { key: "featured_program_text", label: "Featured program description", type: "textarea", rows: 3,
        hint: "One or two sentences. Leave blank to use the default text." },
    ],
  },
  {
    title: "Senior Wellness Day",
    note: "Shown on the Senior Wellness Day page, the Seniors page, and the home page card. Date and location appear only when filled in.",
    items: [
      { key: "wellness_day_status", label: "Badge text", hint: "e.g. \"Coming spring 2027\". Leave blank to use the default." },
      { key: "wellness_day_date", label: "Date", hint: "e.g. \"Saturday, May 15, 2027, 10 AM – 2 PM\". Leave blank until it's set." },
      { key: "wellness_day_location", label: "Location", hint: "Venue name and neighborhood. Leave blank until it's set." },
    ],
  },
  {
    title: "Research",
    items: [{ key: "research_status", label: "Current research status", hint: "Shown on the Research page, e.g. \"In development — no active studies.\"" }],
  },
  {
    title: "Social media links",
    items: [
      { key: "social_facebook", label: "Facebook page URL", type: "url" },
      { key: "social_instagram", label: "Instagram URL", type: "url" },
      { key: "social_youtube", label: "YouTube URL", type: "url" },
    ],
  },
  {
    title: "\"As featured in\" links",
    note: "The outlet names always appear. Add a link to make each one clickable.",
    items: [
      { key: "press_globe_url", label: "The Boston Globe article URL", type: "url" },
      { key: "press_wcvb_url", label: "WCVB Channel 5 Chronicles segment URL", type: "url" },
    ],
  },
  {
    title: "Founder page",
    note: "The founder's SHORT bio (About page card) is edited under Team → Joseph Gallop.",
    items: [
      { key: "founder_full_bio", label: "Full bio", type: "textarea", rows: 18,
        hint: "Separate paragraphs with a blank line. Start a line with \"## \" to make it a section heading (e.g. \"## Lineage and training\"). Write a link as [link text](https://example.org). Please double-check lineage names and dates." },
      { key: "founder_credentials", label: "Credentials", type: "textarea", rows: 7, hint: "One credential per line." },
    ],
  },
];

export function SettingsScreen() {
  useTitle("Site settings");
  const { actions } = useStore();
  const [rows, setRows] = useState(null);
  const [values, setValues] = useState({});
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () =>
    adminApi.get("/admin/settings", { params: { per_page: 500 } }).then((d) => {
      const map = Object.fromEntries(d.items.map((s) => [s.key, s]));
      setRows(map);
      setValues(Object.fromEntries(d.items.map((s) => [s.key, s.value])));
    }).catch(setError);
  useEffect(() => { load(); }, []);

  if (error) return <ErrorNote error={error} onRetry={load} />;
  if (!rows) return <Loading />;

  const changed = GROUPS.flatMap((g) => g.items).filter((i) => (values[i.key] ?? "") !== (rows[i.key] ? rows[i.key].value : ""));

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatus("");
    try {
      for (const item of changed) {
        const value = (values[item.key] || "").trim();
        if (rows[item.key]) await adminApi.patch(`/admin/settings/${rows[item.key].id}`, { value });
        else await adminApi.post("/admin/settings", { key: item.key, value, is_public: true });
      }
      await load();
      actions.refreshSiteContent();
      setStatus(changed.length ? `Saved ${changed.length} change${changed.length === 1 ? "" : "s"}. The website shows them right away.` : "No changes to save.");
    } catch (err) {
      setStatus(`Couldn't save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <h1>Site settings &amp; text</h1>
      <p className="admin-help">These values appear on the public website. Blank links are hidden automatically.</p>
      {status && <div className="alert alert-info" role="status"><p>{status}</p></div>}
      <form onSubmit={save} className="admin-form">
        {GROUPS.map((g) => (
          <fieldset key={g.title} className="panel settings-group">
            <legend><h2 style={{ margin: 0 }}>{g.title}</h2></legend>
            {g.note && <p className="muted">{g.note} {g.title === "Founder page" && <Link to="/admin/team">Go to Team</Link>}</p>}
            {g.items.map((i) => (
              <div className="field" key={i.key}>
                <label htmlFor={`set-${i.key}`}>{i.label}</label>
                {i.hint && <span className="hint" id={`set-${i.key}-hint`}>{i.hint}</span>}
                {i.type === "select" ? (
                  <select id={`set-${i.key}`} aria-describedby={i.hint ? `set-${i.key}-hint` : undefined}
                    value={values[i.key] ?? i.options[0][0]} onChange={(e) => setValues((v) => ({ ...v, [i.key]: e.target.value }))}>
                    {i.options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                ) : i.type === "textarea" ? (
                  <textarea id={`set-${i.key}`} rows={i.rows || 4} aria-describedby={i.hint ? `set-${i.key}-hint` : undefined}
                    value={values[i.key] ?? ""} onChange={(e) => setValues((v) => ({ ...v, [i.key]: e.target.value }))} />
                ) : (
                  <input id={`set-${i.key}`} type={i.type || "text"} aria-describedby={i.hint ? `set-${i.key}-hint` : undefined}
                    value={values[i.key] ?? ""} onChange={(e) => setValues((v) => ({ ...v, [i.key]: e.target.value }))} />
                )}
              </div>
            ))}
          </fieldset>
        ))}
        <div className="admin-actions sticky-actions">
          <button type="submit" className="btn btn-lg" disabled={saving}>{saving ? "Saving…" : `Save changes${changed.length ? ` (${changed.length})` : ""}`}</button>
        </div>
      </form>
    </>
  );
}
