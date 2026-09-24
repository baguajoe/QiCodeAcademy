import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { Honeypot, PageBanner } from "../component/common";
import { SiteImage } from "../component/Photo";

const PRESETS = [25, 50, 100, 250];
const DESIGNATIONS = ["general", "youth", "senior", "research"];

function TaxStatus() {
  const { actions } = useStore();
  const text = actions.setting("tax_status");
  return text ? <p className="small muted tax-status">{text}</p> : null;
}

export default function Donate() {
  const { t, i18n } = useTranslation();
  useSeo({ title: t("donate.title"), description: t("donate.lead"), imageSlot: "donate" });
  const [recurring, setRecurring] = useState(false);
  const [preset, setPreset] = useState("50");
  const [custom, setCustom] = useState("");
  const [designation, setDesignation] = useState("general");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [website, setWebsite] = useState("");
  const [status, setStatus] = useState({ state: "idle", message: "" });
  const alertRef = useRef(null);

  const amount = preset === "custom" ? Number(custom) : Number(preset);
  const valid = Number.isFinite(amount) && amount >= 1 && amount <= 25000;
  const money = (n) => new Intl.NumberFormat(i18n.language === "en" ? "en-US" : "es-US", { style: "currency", currency: "USD" }).format(n || 0);

  const fail = (message) => {
    setStatus({ state: "error", message });
    setTimeout(() => alertRef.current && alertRef.current.focus(), 30);
  };

  const submit = async (e) => {
    e.preventDefault();
    if (status.state === "sending") return;
    if (!valid) return fail(t("donate.amountError"));
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return fail(t("forms.invalidEmail"));
    setStatus({ state: "sending", message: t("donate.redirecting") });
    try {
      const data = await api.post("/donations/create-checkout-session", {
        amount: amount.toFixed(2), recurring, designation, donor_name: name, donor_email: email, website,
      });
      if (data && data.url) window.location.assign(data.url);
      else setStatus({ state: "idle", message: "" });
    } catch (err) {
      if (err.status === 503) fail(t("donate.unavailable"));
      else if (err.status === 429) fail(t("errors.rateLimit"));
      else if (err.status === 400) fail((err.errors.amount && err.errors.amount[0]) || err.message || t("errors.form"));
      else if (err.status === 0) fail(t("errors.network"));
      else fail(err.message || t("errors.generic"));
    }
  };

  const sending = status.state === "sending";
  return (
    <div className="theme-community">
      <PageBanner title={t("donate.title")} lead={t("donate.lead")} />
      <section className="section">
        <div className="container donate-layout">
          <div className="donate-photo">
            <SiteImage slot="donate" sizes="(min-width: 56rem) 40vw, 100vw" priority />
          </div>
          <form className="panel donate-form" onSubmit={submit} noValidate aria-busy={sending} aria-labelledby="donate-form-title">
            <h2 id="donate-form-title">{t("donate.formTitle")}</h2>
            {status.state === "error" && (
              <div className="alert alert-error" role="alert" tabIndex={-1} ref={alertRef}><p>{status.message}</p></div>
            )}
            {sending && <div className="alert alert-info" role="status"><p>{status.message}</p></div>}
            <Honeypot idPrefix="donate" value={website} onChange={(e) => setWebsite(e.target.value)} />

            <fieldset className="field">
              <legend>{t("donate.frequency")}</legend>
              <div className="toggle-radios">
                {[false, true].map((r) => (
                  <label key={String(r)} className={`toggle-option ${recurring === r ? "is-on" : ""}`}>
                    <input type="radio" name="frequency" checked={recurring === r} onChange={() => setRecurring(r)} />
                    <span>{r ? t("donate.monthly") : t("donate.oneTime")}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset className="field">
              <legend>{t("donate.amount")}{recurring ? ` (${t("donate.perMonth").trim()})` : ""}</legend>
              <div className="amount-grid">
                {PRESETS.map((p) => (
                  <label key={p} className={`toggle-option ${preset === String(p) ? "is-on" : ""}`}>
                    <input type="radio" name="amount" value={p} checked={preset === String(p)} onChange={() => setPreset(String(p))} />
                    <span>${p}</span>
                  </label>
                ))}
                <label className={`toggle-option ${preset === "custom" ? "is-on" : ""}`}>
                  <input type="radio" name="amount" value="custom" checked={preset === "custom"} onChange={() => setPreset("custom")} />
                  <span>{t("donate.custom")}</span>
                </label>
              </div>
              {preset === "custom" && (
                <div className="field" style={{ marginTop: "1rem" }}>
                  <label htmlFor="donate-custom">{t("donate.customLabel")}</label>
                  <div className="money-input">
                    <span aria-hidden="true">$</span>
                    <input id="donate-custom" type="number" inputMode="decimal" min="1" max="25000" step="1" value={custom}
                      aria-invalid={custom && !valid ? "true" : undefined} onChange={(e) => setCustom(e.target.value)} autoFocus />
                  </div>
                </div>
              )}
            </fieldset>

            <fieldset className="field">
              <legend>{t("donate.designation")}</legend>
              <div className="choice-grid">
                {DESIGNATIONS.map((d) => (
                  <label key={d} className="check choice-card">
                    <input type="radio" name="designation" checked={designation === d} onChange={() => setDesignation(d)} />
                    <span>{t(`donate.designations.${d}`)}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="grid grid-2" style={{ gap: "0 1rem" }}>
              <div className="field">
                <label htmlFor="donate-name">{t("donate.nameLabel")} <span className="muted small">({t("common.optional")})</span></label>
                <input id="donate-name" type="text" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="field">
                <label htmlFor="donate-email">{t("donate.emailLabel")} <span className="muted small">({t("common.optional")})</span></label>
                <input id="donate-email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
            </div>

            {valid && (
              <p className="donate-summary" aria-live="polite">
                {t("donate.summary", { amount: money(amount), period: recurring ? t("donate.perMonth") : "", designation: t(`donate.designations.${designation}`) })}
              </p>
            )}
            <button type="submit" className="btn btn-donate btn-lg btn-block" disabled={sending}>
              {sending ? t("donate.redirecting") : recurring ? t("donate.submitMonthly") : t("donate.submit")}
            </button>
            <p className="small muted" style={{ marginTop: "1rem" }}><span aria-hidden="true">🔒 </span>{t("donate.stripeNote")}</p>
            <TaxStatus />
          </form>
        </div>
      </section>
    </div>
  );
}

export function DonateThanks() {
  const { t } = useTranslation();
  useSeo({ title: t("donate.thanksTitle"), noindex: true });
  return (
    <section className="section">
      <div className="container container-narrow center">
        <h1>{t("donate.thanksTitle")}</h1>
        <p className="lead">{t("donate.thanksBody")}</p>
        <TaxStatus />
        <div className="cluster" style={{ justifyContent: "center" }}>
          <Link className="btn" to="/">{t("donate.thanksBack")}</Link>
          <Link className="btn btn-outline" to="/get-involved">{t("common.getInvolved")}</Link>
        </div>
      </div>
    </section>
  );
}

export function DonateCancelled() {
  const { t } = useTranslation();
  useSeo({ title: t("donate.cancelledTitle"), noindex: true });
  return (
    <section className="section">
      <div className="container container-narrow center">
        <h1>{t("donate.cancelledTitle")}</h1>
        <p className="lead">{t("donate.cancelledBody")}</p>
        <div className="cluster" style={{ justifyContent: "center" }}>
          <Link className="btn btn-donate" to="/donate">{t("donate.tryAgain")}</Link>
          <Link className="btn btn-outline" to="/contact">{t("nav.contact")}</Link>
        </div>
      </div>
    </section>
  );
}
