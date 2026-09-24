import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { adminApi } from "../api";
import { ErrorNote, Loading } from "../component/common";
import { RESOURCES, ROLES, newRecordDefaults } from "./resources";
import { ImageField } from "./ImageField";
import { RichTextEditor } from "./RichTextEditor";
import { useProgramOptions } from "./ResourceList";
import { useTitle } from "./AdminApp";
import { useStore } from "../store/appContext";
import NotFound from "../pages/NotFound";

// datetime-local wants "YYYY-MM-DDTHH:MM" (events are stored in Boston time already).
const toInputDateTime = (v) => (v ? v.slice(0, 16) : "");

function Field({ f, values, set, errors, programs, formId, isNew }) {
  const id = `${formId}-${f.key}`;
  const value = values[f.key];
  const err = errors[f.key];
  const required = f.required || (isNew && f.requiredOnCreate);
  const described = [f.hint && `${id}-hint`, err && `${id}-err`].filter(Boolean).join(" ") || undefined;
  const common = { id, "aria-invalid": err ? "true" : undefined, "aria-describedby": described };
  const disabled = f.disabledIf ? f.disabledIf(values) : false;

  if (f.type === "image") {
    return (
      <ImageField id={id} label={f.label} value={value} required={f.required}
        onChange={(url) => set(f.key, url)}
        alt={f.altKey ? values[f.altKey] : undefined}
        onAltChange={f.altKey ? (v) => set(f.altKey, v) : undefined}
        note={f.altFromName ? "Alt text is created automatically from the name." : undefined}
        folder={formId.replace(/^edit-/, "")} error={err} altError={f.altKey ? errors[f.altKey] : undefined} />
    );
  }
  if (f.type === "richtext") {
    return <RichTextEditor id={id} label={f.label} value={value} onChange={(v) => set(f.key, v)} error={err} />;
  }
  if (f.type === "bool") {
    return (
      <div className="field">
        <label className="check" htmlFor={id}>
          <input type="checkbox" {...common} checked={!!value} disabled={disabled} onChange={(e) => set(f.key, e.target.checked)} />
          <span>{f.label}</span>
        </label>
        {f.hint && <span className="hint" id={`${id}-hint`}>{f.hint}</span>}
        {err && <p className="field-error" id={`${id}-err`}>{err}</p>}
      </div>
    );
  }
  if (f.type === "roles") {
    const list = value || [];
    return (
      <fieldset className="field">
        <legend>{f.label}{required && <span className="required-mark" aria-hidden="true">*</span>}</legend>
        <div className="choice-grid">
          {ROLES.map(([v, l]) => (
            <label key={v} className="check choice-card">
              <input type="checkbox" checked={list.includes(v)} onChange={() => set(f.key, list.includes(v) ? list.filter((x) => x !== v) : [...list, v])} />
              <span>{l}</span>
            </label>
          ))}
        </div>
        {err && <p className="field-error">{err}</p>}
      </fieldset>
    );
  }

  let input;
  if (f.type === "readonly") {
    input = <p id={id} className="readonly">{value || "—"}</p>;
  } else if (f.type === "lines") {
    // Edited as one-item-per-line text; the API splits it into a list.
    input = <textarea {...common} rows={Math.min(14, Math.max(4, (Array.isArray(value) ? value.length : 3) + 1))}
      value={Array.isArray(value) ? value.join("\n") : value ?? ""} onChange={(e) => set(f.key, e.target.value)} />;
  } else if (f.type === "textarea") {
    input = <textarea {...common} rows={f.key === "bio" ? 8 : 5} value={value ?? ""} onChange={(e) => set(f.key, e.target.value)} />;
  } else if (f.type === "select" || f.type === "program") {
    const opts = f.type === "program" ? programs.map((p) => [p.id, p.title]) : f.options;
    input = (
      <select {...common} value={value ?? ""} onChange={(e) => set(f.key, f.type === "program" ? Number(e.target.value) || "" : e.target.value)}>
        <option value="">Choose…</option>
        {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    );
  } else if (f.type === "money") {
    input = (
      <input {...common} type="number" min="0" step="0.01" inputMode="decimal"
        value={value === null || value === undefined || value === "" ? "" : (value / 100).toFixed(2)}
        onChange={(e) => set(f.key, e.target.value === "" ? "" : Math.round(Number(e.target.value) * 100))} />
    );
  } else {
    const type = { number: "number", date: "date", datetime: "datetime-local", email: "email", tel: "tel", url: "url", password: "password" }[f.type] || "text";
    const shown = f.type === "datetime" ? toInputDateTime(value) : value ?? "";
    input = (
      <>
        <input {...common} type={type} value={shown} list={f.list ? `${id}-list` : undefined}
          autoComplete={f.type === "password" ? "new-password" : "off"}
          onChange={(e) => set(f.key, f.type === "number" ? (e.target.value === "" ? null : Number(e.target.value)) : e.target.value)} />
        {f.list && <datalist id={`${id}-list`}>{f.list.map((o) => <option key={o} value={o} />)}</datalist>}
      </>
    );
  }
  return (
    <div className="field">
      <label htmlFor={id}>{f.label}{required && <span className="required-mark" aria-hidden="true">*</span>}</label>
      {f.hint && <span className="hint" id={`${id}-hint`}>{f.hint}</span>}
      {input}
      {err && <p className="field-error" id={`${id}-err`}>{err}</p>}
    </div>
  );
}

export function ResourceForm() {
  const { resource, id } = useParams();
  const cfg = RESOURCES[resource];
  const isNew = !id;
  const navigate = useNavigate();
  const { actions } = useStore();
  const [values, setValues] = useState(isNew ? newRecordDefaults(resource) : null);
  const [loadError, setLoadError] = useState(null);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState({ kind: "", text: "" });
  const [saving, setSaving] = useState(false);
  const statusRef = useRef(null);
  const needsPrograms = cfg && cfg.fields.some((f) => f.type === "program");
  const programs = useProgramOptions();
  useTitle(cfg ? `${isNew ? "Add" : "Edit"} ${cfg.singular}` : "Not found");

  useEffect(() => {
    if (!cfg || isNew) return;
    adminApi.get(`/admin/${resource}/${id}`).then(async (row) => {
      setValues(row);
      if (cfg.autoMarkRead && row.is_read === false) {
        await adminApi.patch(`/admin/${resource}/${id}`, { is_read: true }).catch(() => {});
        setValues((v) => ({ ...v, is_read: true }));
      }
    }).catch(setLoadError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resource, id]);

  if (!cfg) return <NotFound />;
  if (loadError) return loadError.status === 404 ? <NotFound /> : <ErrorNote error={loadError} />;
  if (!values) return <Loading />;

  const set = (k, v) => {
    setValues((s) => ({ ...s, [k]: v }));
    setErrors((e) => ({ ...e, [k]: undefined }));
  };
  const visible = cfg.fields.filter((f) => !f.showIf || f.showIf(values));

  const announce = (kind, text) => {
    setStatus({ kind, text });
    setTimeout(() => statusRef.current && statusRef.current.focus(), 30);
  };

  const save = async (e) => {
    e.preventDefault();
    // Client checks: required fields and alt text for photos.
    const errs = {};
    visible.forEach((f) => {
      const v = values[f.key];
      if ((f.required || (isNew && f.requiredOnCreate)) && (v === undefined || v === null || v === "" || (Array.isArray(v) && !v.length)))
        errs[f.key] = "This field is required.";
      if (f.type === "image" && f.altKey && v && !(values[f.altKey] || "").trim())
        errs[f.altKey] = "Please describe the photo before saving.";
    });
    if (Object.keys(errs).length) {
      setErrors(errs);
      return announce("error", "Please fix the highlighted fields.");
    }
    const payload = {};
    visible.forEach((f) => {
      if (f.type === "readonly") return;
      if (f.type === "password" && !values[f.key]) return;
      payload[f.key] = values[f.key];
      if (f.altKey) payload[f.altKey] = values[f.altKey] || "";
    });
    // Hidden type-specific registration fields are cleared so the API rules hold.
    cfg.fields.filter((f) => f.showIf && !f.showIf(values)).forEach((f) => { payload[f.key] = null; });

    setSaving(true);
    try {
      const saved = isNew
        ? await adminApi.post(`/admin/${resource}`, payload)
        : await adminApi.patch(`/admin/${resource}/${id}`, payload);
      setValues({ ...saved, password: "" });
      setErrors({});
      if (["settings", "site-images"].includes(resource)) actions.refreshSiteContent();
      if (isNew) navigate(`/admin/${resource}/${saved.id}`, { replace: true, state: { saved: true } });
      announce("success", "Saved.");
    } catch (err) {
      const fieldErrs = Object.fromEntries(Object.entries(err.errors || {}).map(([k, v]) => [k, [].concat(v).join(" ")]));
      setErrors(fieldErrs);
      announce("error", err.status === 409 ? "That conflicts with an existing record (for example, the web address or email is already used)." : err.message || "Couldn't save.");
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete this ${cfg.singular}? This can't be undone.`)) return;
    try {
      await adminApi.del(`/admin/${resource}/${id}`);
      navigate(`/admin/${resource}`, { replace: true });
    } catch (err) {
      announce("error", err.message || "Couldn't delete.");
    }
  };

  const title = isNew ? `Add ${cfg.singular}` : values.title || values.name || (values.participant_first_name ? `${values.participant_first_name} ${values.participant_last_name}` : `${cfg.singular} #${id}`);
  const publicLink = !isNew && values.slug && { programs: `/register/${values.slug}`, events: `/events/${values.slug}`, news: `/news/${values.slug}` }[resource];

  return (
    <>
      <nav className="breadcrumb" aria-label="Breadcrumb"><Link to={`/admin/${resource}`}>← All {cfg.label.toLowerCase()}</Link></nav>
      <div className="admin-head">
        <h1>{title}</h1>
        {publicLink && <a className="btn btn-outline" href={publicLink} target="_blank" rel="noopener noreferrer">View on website ↗</a>}
      </div>
      {cfg.help && <p className="admin-help">{cfg.help}</p>}
      {status.text && (
        <div className={`alert ${status.kind === "success" ? "alert-success" : "alert-error"}`} role={status.kind === "success" ? "status" : "alert"} tabIndex={-1} ref={statusRef}>
          <p>{status.text}</p>
        </div>
      )}
      {!isNew && values.created_at && <p className="muted small">Created {new Date(values.created_at).toLocaleString()}</p>}
      <form className="admin-form panel" onSubmit={save} noValidate>
        {visible.map((f) => (
          <Field key={f.key} f={f} values={values} set={set} errors={errors} programs={needsPrograms ? programs : []} formId={`edit-${resource}`} isNew={isNew} />
        ))}
        <div className="cluster admin-actions">
          <button type="submit" className="btn btn-lg" disabled={saving}>{saving ? "Saving…" : "Save"}</button>
          <Link className="btn btn-outline btn-lg" to={`/admin/${resource}`}>Cancel</Link>
          {!isNew && <button type="button" className="btn btn-lg btn-danger" onClick={remove}>Delete</button>}
        </div>
      </form>
    </>
  );
}
