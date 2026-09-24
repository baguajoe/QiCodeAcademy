// Multi-step program registration.
// Youth: a PARENT/GUARDIAN fills it out; we never collect the child's own email/phone.
// Senior: the participant (or a helper) fills it out.
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { Empty, ErrorNote, Loading, WellnessDisclaimer } from "../component/common";
import { CheckboxField, FormStatus, RadioGroup, SelectField, TextArea, TextField, useForm } from "../component/Form";
import { Honeypot } from "../component/common";
import { SeatsBadge, placeText } from "../component/Cards";
import { formatDateRange } from "../format";

const STEP_FIELDS = {
  who: ["type"],
  guardian: ["guardian_name", "guardian_email", "guardian_phone"],
  child: ["participant_first_name", "participant_last_name", "grade"],
  you: ["participant_first_name", "participant_last_name", "email", "phone"],
  emergency: ["emergency_contact_name", "emergency_contact_phone"],
  consent: ["photo_consent", "guardian_consent"],
  comfort: ["comfort_notes", "photo_consent"],
};

const INITIAL = {
  type: "", guardian_name: "", guardian_email: "", guardian_phone: "",
  participant_first_name: "", participant_last_name: "", grade: "",
  email: "", phone: "", emergency_contact_name: "", emergency_contact_phone: "",
  photo_consent: null, guardian_consent: false, comfort_notes: "",
};

function ChooseProgram() {
  const { t } = useTranslation();
  const { data, error, loading, reload } = useApi(() => api.get("/programs"), []);
  useSeo({ title: t("register.title"), description: t("register.chooseLead") });
  return (
    <section className="section">
      <div className="container container-narrow">
        <h1>{t("register.chooseProgram")}</h1>
        <p className="lead">{t("register.chooseLead")}</p>
        {loading && <Loading />}
        {error && <ErrorNote error={error} onRetry={reload} />}
        {data && !data.items.length && <Empty>{t("common.comingSoon")}</Empty>}
        {data && data.items.length > 0 && (
          <ul className="stack" style={{ listStyle: "none", padding: 0 }}>
            {data.items.map((p) => (
              <li key={p.id} className={`card card-accent theme-${p.division}`} style={{ padding: "1.25rem" }}>
                <div className="cluster" style={{ justifyContent: "space-between" }}>
                  <div>
                    <span className="badge">{t(`divisions.${p.division}.short`)}</span> <SeatsBadge program={p} />
                    <h2 style={{ fontSize: "1.25rem", margin: "0.5rem 0 0.25rem" }}>{p.title}</h2>
                    <p className="muted" style={{ margin: 0 }}>{[p.schedule, placeText(p.location, p.neighborhood)].filter(Boolean).join(" · ")}</p>
                  </div>
                  <Link className="btn" to={`/register/${p.slug}`}>{t("common.register")}<span className="sr-only">: {p.title}</span></Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function Progress({ steps, current }) {
  const { t } = useTranslation();
  return (
    <ol className="steps" aria-label={t("register.stepOf", { step: current + 1, total: steps.length })}>
      {steps.map((s, i) => (
        <li key={s} className={i < current ? "done" : i === current ? "current" : ""} aria-current={i === current ? "step" : undefined}>
          <span className="n" aria-hidden="true">{i < current ? "✓" : i + 1}</span>
          <span className="t">{t(`register.steps.${s}`)}</span>
        </li>
      ))}
    </ol>
  );
}

function Review({ values, program }) {
  const { t } = useTranslation();
  const youth = values.type === "youth";
  const rows = youth
    ? [[t("register.guardianName"), values.guardian_name], [t("register.guardianEmail"), values.guardian_email],
       [t("register.guardianPhone"), values.guardian_phone],
       [t("register.steps.child"), `${values.participant_first_name} ${values.participant_last_name}`],
       [t("register.grade"), values.grade]]
    : [[t("register.steps.you"), `${values.participant_first_name} ${values.participant_last_name}`],
       [t("register.seniorEmail"), values.email], [t("register.seniorPhone"), values.phone]];
  rows.push([t("register.steps.emergency"), `${values.emergency_contact_name} — ${values.emergency_contact_phone}`]);
  return (
    <section className="review-box" aria-labelledby="review-title">
      <h3 id="review-title">{t("register.review")}: {program.title}</h3>
      <dl>
        {rows.filter(([, v]) => v && v.trim()).map(([k, v]) => (<div key={k}><dt>{k}</dt><dd>{v}</dd></div>))}
      </dl>
    </section>
  );
}

function RegistrationForm({ program }) {
  const { t } = useTranslation();
  const fixedType = program.division === "youth" ? "youth" : program.division === "senior" ? "senior" : null;
  const [result, setResult] = useState(null);
  const [step, setStep] = useState(0);
  const headingRef = useRef(null);

  const form = useForm({
    formId: "register",
    endpoint: "/registrations",
    initial: { ...INITIAL, type: fixedType || "" },
    required: [],
    emails: ["guardian_email", "email"],
    validate: (v) => {
      const e = {};
      const req = (f) => { if (!String(v[f] ?? "").trim()) e[f] = t("forms.requiredField"); };
      if (!v.type) e.type = t("forms.requiredField");
      ["participant_first_name", "participant_last_name", "emergency_contact_name", "emergency_contact_phone"].forEach(req);
      if (v.type === "youth") {
        ["guardian_name", "guardian_email", "guardian_phone", "grade"].forEach(req);
        if (!v.guardian_consent) e.guardian_consent = t("forms.requiredField");
      }
      if (v.type === "senior" && !v.email.trim() && !v.phone.trim()) e.email = t("register.contactHint");
      if (v.photo_consent === null) e.photo_consent = t("forms.requiredField");
      return e;
    },
    transform: (v) => {
      const base = {
        program_id: program.id, type: v.type,
        participant_first_name: v.participant_first_name, participant_last_name: v.participant_last_name,
        emergency_contact_name: v.emergency_contact_name, emergency_contact_phone: v.emergency_contact_phone,
        photo_consent: v.photo_consent === true,
      };
      // Youth: guardian contact only — the child's email/phone are never sent.
      return v.type === "youth"
        ? { ...base, guardian_name: v.guardian_name, guardian_email: v.guardian_email, guardian_phone: v.guardian_phone,
            grade: v.grade, guardian_consent: v.guardian_consent === true }
        : { ...base, email: v.email, phone: v.phone, comfort_notes: v.comfort_notes };
    },
    onSuccess: (data) => setResult(data),
  });

  const type = form.values.type;
  const steps = [
    ...(fixedType ? [] : ["who"]),
    ...(type === "senior" ? ["you", "emergency", "comfort"] : ["guardian", "child", "emergency", "consent"]),
  ];
  const current = steps[Math.min(step, steps.length - 1)];
  const last = step >= steps.length - 1;

  useEffect(() => {
    if (headingRef.current && step > 0) headingRef.current.focus();
  }, [step]);

  // If the server rejects a field, jump back to the step that contains it.
  useEffect(() => {
    const bad = Object.keys(form.errors).filter((k) => form.errors[k]);
    if (!bad.length || form.status !== "error") return;
    const idx = steps.findIndex((s) => STEP_FIELDS[s].some((f) => bad.includes(f)));
    if (idx >= 0 && idx !== step) setStep(idx);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.errors]);

  const next = () => {
    const fields = current === "you" ? STEP_FIELDS.you : STEP_FIELDS[current];
    if (form.checkFields(fields)) setStep((s) => s + 1);
  };

  if (result) {
    const waitlisted = result.waitlisted || result.status === "waitlist";
    return (
      <div className={`alert ${waitlisted ? "alert-warning" : "alert-success"}`} role="status" tabIndex={-1} ref={(el) => el && el.focus()}>
        <h2>{waitlisted ? t("register.waitlistTitle") : t("register.successTitle")}</h2>
        <p>{waitlisted ? t("register.waitlistBody", { program: program.title }) : t("register.successBody", { program: program.title })}</p>
        <p>{t("register.emailNote")}</p>
        <div className="cluster">
          <button type="button" className="btn" onClick={() => { form.reset(); setResult(null); setStep(0); }}>{t("register.another")}</button>
          <Link className="btn btn-outline" to={`/programs/${{ youth: "youth", senior: "seniors" }[program.division] || "intergenerational"}`}>{t("register.backToPrograms")}</Link>
        </div>
      </div>
    );
  }

  const onSubmit = (e) => {
    e.preventDefault();
    if (!last) return next();
    form.submit();
  };
  const grades = ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12"];
  const ordinal = (g) => ({ "3": "3rd" }[g] || `${g}th`);

  return (
    <form id="register" onSubmit={onSubmit} noValidate aria-busy={form.status === "sending"} className="register-form">
      <Progress steps={steps} current={step} />
      <FormStatus form={form} labels={{}} />
      <Honeypot idPrefix="register" value={form.website} onChange={(e) => form.setWebsite(e.target.value)} />
      <p className="muted small">{t("forms.requiredNote")}</p>

      <h2 ref={headingRef} tabIndex={-1} className="step-title">
        <span className="muted small" style={{ display: "block", fontFamily: "var(--font-body)", fontWeight: 700 }}>
          {t("register.stepOf", { step: step + 1, total: steps.length })}
        </span>
        {t(`register.steps.${current}`)}
      </h2>

      {current === "who" && (
        <RadioGroup form={form} name="type" legend={t("register.whoTitle")} required
          options={[{ value: "youth", label: t("register.whoYouth") }, { value: "senior", label: t("register.whoSenior") }]} />
      )}

      {current === "guardian" && (
        <>
          <p className="alert alert-info">{t("register.youthIntro")}</p>
          <TextField form={form} name="guardian_name" label={t("register.guardianName")} required autoComplete="name" />
          <TextField form={form} name="guardian_email" type="email" label={t("register.guardianEmail")} required autoComplete="email" />
          <TextField form={form} name="guardian_phone" type="tel" label={t("register.guardianPhone")} required autoComplete="tel" hint={t("forms.phoneHint")} />
        </>
      )}

      {current === "child" && (
        <>
          <TextField form={form} name="participant_first_name" label={t("register.childFirst")} required autoComplete="off" />
          <TextField form={form} name="participant_last_name" label={t("register.childLast")} required autoComplete="off" />
          <SelectField form={form} name="grade" label={t("register.grade")} required placeholder={t("register.gradeChoose")}
            options={[...grades.map((g) => ({ value: g, label: ordinal(g) })), { value: "other", label: t("register.gradeOther") }]} />
        </>
      )}

      {current === "you" && (
        <>
          <TextField form={form} name="participant_first_name" label={t("register.seniorFirst")} required autoComplete="given-name" />
          <TextField form={form} name="participant_last_name" label={t("register.seniorLast")} required autoComplete="family-name" />
          <p className="hint" id="contact-hint"><strong>{t("register.contactHint")}</strong></p>
          <TextField form={form} name="email" type="email" label={t("register.seniorEmail")} autoComplete="email" />
          <TextField form={form} name="phone" type="tel" label={t("register.seniorPhone")} autoComplete="tel" hint={t("forms.phoneHint")} />
        </>
      )}

      {current === "emergency" && (
        <>
          <TextField form={form} name="emergency_contact_name" label={t("register.emergencyName")} required autoComplete="off" />
          <TextField form={form} name="emergency_contact_phone" type="tel" label={t("register.emergencyPhone")} required autoComplete="off" hint={t("forms.phoneHint")} />
        </>
      )}

      {(current === "consent" || current === "comfort") && (
        <>
          {current === "comfort" && (
            <TextArea form={form} name="comfort_notes" label={t("register.comfortLabel")} hint={t("register.comfortHint")} rows={4} maxLength={2000} />
          )}
          <RadioGroup form={form} name="photo_consent" legend={t("register.photoConsentLegend")} required
            options={[{ value: true, label: t("register.photoConsentYes") }, { value: false, label: t("register.photoConsentNo") }]} />
          {current === "consent" && (
            <CheckboxField form={form} name="guardian_consent" label={t("register.guardianConsent")} required />
          )}
          <Review values={form.values} program={program} />
          {current === "comfort" && <WellnessDisclaimer />}
        </>
      )}

      <div className="cluster step-actions">
        {step > 0 && (
          <button type="button" className="btn btn-outline btn-lg" onClick={() => { form.setStatus("idle"); setStep((s) => s - 1); }}>
            ← {t("common.back")}
          </button>
        )}
        <button type="submit" className="btn btn-lg" disabled={form.status === "sending"}>
          {last ? (form.status === "sending" ? t("common.sending") : t("register.submit")) : `${t("common.next")} →`}
        </button>
      </div>
    </form>
  );
}

export default function Register() {
  const { t } = useTranslation();
  const { slug } = useParams();
  const { data: program, error, loading, reload } = useApi(() => (slug ? api.get(`/programs/${slug}`) : Promise.resolve(null)), [slug]);
  useSeo({ title: program ? `${t("register.title")}: ${program.title}` : t("register.title"), noindex: true });

  if (!slug) return <ChooseProgram />;
  if (loading) return <div className="container section"><Loading /></div>;
  if (error) {
    return (
      <section className="section"><div className="container container-narrow">
        <h1>{t("register.title")}</h1>
        {error.status === 404 ? <p className="alert alert-error">{t("register.programNotFound")}</p> : <ErrorNote error={error} onRetry={reload} />}
        <Link to="/register">{t("register.chooseProgram")}</Link>
      </div></section>
    );
  }

  const dates = formatDateRange(program.start_date, program.end_date);
  return (
    <div className={`theme-${program.division}`}>
      <section className="banner banner-plain">
        <div className="container banner-content">
          <span className="motto">{t(`divisions.${program.division}.short`)}</span>
          <h1>{t("register.title")}: {program.title}</h1>
          <p className="lead">{[program.schedule, dates, placeText(program.location, program.neighborhood)].filter(Boolean).join(" · ")}</p>
          <div><SeatsBadge program={program} /></div>
        </div>
      </section>
      <section className="section">
        <div className="container container-narrow">
          {!program.is_active ? (
            <p className="alert alert-warning">{t("register.closed")}</p>
          ) : (
            <>
              {program.is_full && <p className="alert alert-warning">{t("register.fullNotice")}</p>}
              <RegistrationForm program={program} />
            </>
          )}
        </div>
      </section>
    </div>
  );
}
