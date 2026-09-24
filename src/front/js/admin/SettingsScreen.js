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
        hint: "Shown in the footer and on the Donate pages. Update this when the IRS grants 501(c)(3) status. Don't promise deductibility unless it's confirmed." },
      { key: "org_contact_email", label: "Organization email", type: "email", hint: "Shown on the Contact page and footer. Leave blank to hide. Never use a personal address." },
      { key: "org_contact_phone", label: "Organization phone", type: "tel", hint: "Shown on the Contact page and footer. Leave blank to hide. Never use a personal number." },
      { key: "teaching_locations", label: "Where we teach", type: "textarea", rows: 4,
        hint: "Shown on the Contact page. One place per line, names only (e.g. \"Codman Square Library\"). Do not add street addresses." },
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
        hint: "Separate paragraphs with a blank line. Start a line with \"## \" to make it a section heading (e.g. \"## Lineage and training\"). Please double-check lineage names and dates." },
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
                {i.type === "textarea" ? (
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
