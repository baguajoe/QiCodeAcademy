// Accessible form building blocks shared by every public form.
// - Labels tied to inputs; hints/errors via aria-describedby; aria-invalid on errors
// - Error summary (role=alert) with links to each field, focused on failure
// - Success message (role=status) focused on success
// - Honeypot field "website"; submit button disabled while sending
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { Honeypot } from "./common";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function useForm({ initial, endpoint, required = [], emails = [], validate, transform, onSuccess, formId }) {
  const { t } = useTranslation();
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("idle"); // idle | sending | success | error
  const [message, setMessage] = useState("");
  const [website, setWebsite] = useState("");
  const summaryRef = useRef(null);
  const successRef = useRef(null);

  const set = (name, value) => {
    setValues((v) => ({ ...v, [name]: value }));
    if (errors[name]) setErrors((e) => ({ ...e, [name]: undefined }));
  };

  const clientErrors = (vals) => {
    const errs = {};
    required.forEach((f) => {
      const v = vals[f];
      if (v === undefined || v === null || (typeof v === "string" && !v.trim()) || (Array.isArray(v) && !v.length))
        errs[f] = t("forms.requiredField");
    });
    emails.forEach((f) => {
      if (vals[f] && !EMAIL_RE.test(vals[f].trim()) && !errs[f]) errs[f] = t("forms.invalidEmail");
    });
    Object.assign(errs, validate ? validate(vals) || {} : {});
    return Object.fromEntries(Object.entries(errs).filter(([, v]) => v));
  };

  const focusLater = (ref) => setTimeout(() => ref.current && ref.current.focus(), 30);

  const submit = async (e) => {
    if (e) e.preventDefault();
    if (status === "sending") return;
    const errs = clientErrors(values);
    if (Object.keys(errs).length) {
      setErrors(errs);
      setStatus("error");
      setMessage(t("errors.form"));
      focusLater(summaryRef);
      return;
    }
    setStatus("sending");
    setErrors({});
    try {
      const payload = { ...(transform ? transform(values) : values), website };
      const data = await api.post(endpoint, payload);
      setStatus("success");
      setMessage((data && data.message) || t("forms.successTitle"));
      if (onSuccess) onSuccess(data, values);
      else setValues(initial);
      focusLater(successRef);
    } catch (err) {
      const fieldErrs = Object.fromEntries(
        Object.entries(err.errors || {}).map(([k, v]) => [k, Array.isArray(v) ? v.join(" ") : String(v)])
      );
      setErrors(fieldErrs);
      setStatus("error");
      setMessage(err.status === 429 ? t("errors.rateLimit") : err.status === 0 ? t("errors.network")
        : Object.keys(fieldErrs).length ? t("errors.form") : err.message || t("errors.generic"));
      focusLater(summaryRef);
    }
  };

  // For multi-step forms: validate a subset of fields before moving on.
  const checkFields = (fields) => {
    const errs = Object.fromEntries(Object.entries(clientErrors(values)).filter(([k]) => fields.includes(k)));
    setErrors(errs);
    if (Object.keys(errs).length) {
      setStatus("error");
      setMessage(t("errors.form"));
      focusLater(summaryRef);
      return false;
    }
    setStatus("idle");
    return true;
  };

  return { values, set, setValues, errors, setErrors, status, message, submit, website, setWebsite, summaryRef, successRef,
    formId, setStatus, checkFields, reset: () => { setValues(initial); setErrors({}); setStatus("idle"); } };
}

export function FormStatus({ form, labels = {}, successTitle }) {
  const { t } = useTranslation();
  if (form.status === "success") {
    return (
      <div className="alert alert-success" role="status" tabIndex={-1} ref={form.successRef}>
        <h3>{successTitle || t("forms.successTitle")}</h3>
        <p>{form.message}</p>
      </div>
    );
  }
  if (form.status === "error") {
    const entries = Object.entries(form.errors).filter(([, v]) => v);
    return (
      <div className="alert alert-error" role="alert" tabIndex={-1} ref={form.summaryRef}>
        <h3>{t("forms.errorSummary")}</h3>
        <p>{form.message}</p>
        {entries.length > 0 && (
          <ul>
            {entries.map(([k, v]) => (
              <li key={k}>
                <a href={`#${form.formId}-${k}`} onClick={(e) => {
                  e.preventDefault();
                  const el = document.getElementById(`${form.formId}-${k}`);
                  if (el) el.focus();
                }}>
                  {labels[k] ? `${labels[k]}: ` : ""}{v}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }
  return null;
}

function describedBy(id, hint, error) {
  return [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
}

function FieldShell({ id, label, required, hint, error, children }) {
  const { t } = useTranslation();
  return (
    <div className="field">
      <label htmlFor={id}>
        {label}
        {required ? <span className="required-mark" aria-hidden="true">*</span> : <span className="muted small"> ({t("common.optional")})</span>}
      </label>
      {hint && <span className="hint" id={`${id}-hint`}>{hint}</span>}
      {children}
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
    </div>
  );
}

export function TextField({ form, name, label, type = "text", required, hint, autoComplete, inputMode, list, ...rest }) {
  const id = `${form.formId}-${name}`;
  const error = form.errors[name];
  return (
    <FieldShell id={id} label={label} required={required} hint={hint} error={error}>
      <input id={id} name={name} type={type} value={form.values[name] ?? ""} required={required}
        aria-required={required || undefined} aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy(id, hint, error)} autoComplete={autoComplete} inputMode={inputMode} list={list}
        onChange={(e) => form.set(name, e.target.value)} {...rest} />
    </FieldShell>
  );
}

export function TextArea({ form, name, label, required, hint, rows = 5, maxLength }) {
  const id = `${form.formId}-${name}`;
  const error = form.errors[name];
  return (
    <FieldShell id={id} label={label} required={required} hint={hint} error={error}>
      <textarea id={id} name={name} rows={rows} maxLength={maxLength} value={form.values[name] ?? ""} required={required}
        aria-required={required || undefined} aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy(id, hint, error)} onChange={(e) => form.set(name, e.target.value)} />
    </FieldShell>
  );
}

export function SelectField({ form, name, label, required, hint, options, placeholder }) {
  const id = `${form.formId}-${name}`;
  const error = form.errors[name];
  return (
    <FieldShell id={id} label={label} required={required} hint={hint} error={error}>
      <select id={id} name={name} value={form.values[name] ?? ""} required={required}
        aria-required={required || undefined} aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy(id, hint, error)} onChange={(e) => form.set(name, e.target.value)}>
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </FieldShell>
  );
}

export function CheckboxField({ form, name, label, required, error: errorOverride }) {
  const id = `${form.formId}-${name}`;
  const error = errorOverride || form.errors[name];
  return (
    <div className="field">
      <label className="check" htmlFor={id}>
        <input id={id} type="checkbox" checked={!!form.values[name]} aria-invalid={error ? "true" : undefined}
          aria-describedby={error ? `${id}-error` : undefined} aria-required={required || undefined}
          onChange={(e) => form.set(name, e.target.checked)} />
        <span>{label}{required && <span className="required-mark" aria-hidden="true">*</span>}</span>
      </label>
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
    </div>
  );
}

// Group of checkboxes (e.g. volunteer roles) stored as an array.
export function CheckboxGroup({ form, name, legend, options, required, hint }) {
  const id = `${form.formId}-${name}`;
  const error = form.errors[name];
  const value = form.values[name] || [];
  const toggle = (v) => form.set(name, value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  return (
    <fieldset className="field" aria-describedby={describedBy(id, hint, error)}>
      <legend>{legend}{required && <span className="required-mark" aria-hidden="true">*</span>}</legend>
      {hint && <span className="hint" id={`${id}-hint`}>{hint}</span>}
      <div className="choice-grid">
        {options.map((o, i) => (
          <label key={o.value} className="check choice-card" htmlFor={i === 0 ? id : `${id}-${o.value}`}>
            <input id={i === 0 ? id : `${id}-${o.value}`} type="checkbox" checked={value.includes(o.value)}
              onChange={() => toggle(o.value)} aria-invalid={error ? "true" : undefined} />
            <span>{o.label}</span>
          </label>
        ))}
      </div>
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
    </fieldset>
  );
}

// Radio group; first radio carries the field id so error links can focus it.
export function RadioGroup({ form, name, legend, options, required, hint }) {
  const id = `${form.formId}-${name}`;
  const error = form.errors[name];
  return (
    <fieldset className="field" aria-describedby={describedBy(id, hint, error)}>
      <legend>{legend}{required && <span className="required-mark" aria-hidden="true">*</span>}</legend>
      {hint && <span className="hint" id={`${id}-hint`}>{hint}</span>}
      <div className="choice-grid" role="radiogroup" aria-required={required || undefined}>
        {options.map((o, i) => (
          <label key={String(o.value)} className="check choice-card" htmlFor={i === 0 ? id : `${id}-${o.value}`}>
            <input id={i === 0 ? id : `${id}-${o.value}`} type="radio" name={id} checked={form.values[name] === o.value}
              onChange={() => form.set(name, o.value)} aria-invalid={error ? "true" : undefined} />
            <span>{o.label}</span>
          </label>
        ))}
      </div>
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
    </fieldset>
  );
}

export function FormShell({ form, children, submitLabel, labels, successTitle, className = "" }) {
  const { t } = useTranslation();
  const sending = form.status === "sending";
  return (
    <form id={form.formId} className={`form ${className}`} onSubmit={form.submit} noValidate aria-busy={sending}>
      <FormStatus form={form} labels={labels} successTitle={successTitle} />
      <p className="muted small">{t("forms.requiredNote")}</p>
      <Honeypot idPrefix={form.formId} value={form.website} onChange={(e) => form.setWebsite(e.target.value)} />
      {children}
      <button type="submit" className="btn btn-lg" disabled={sending} aria-disabled={sending}>
        {sending ? t("common.sending") : submitLabel || t("common.submit")}
      </button>
    </form>
  );
}
