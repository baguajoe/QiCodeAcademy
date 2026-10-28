// Senior Wellness Day (planned for spring 2027): what we plan to offer, a senior interest list,
// and a form for practitioners, instructors, vendors, volunteers, and sponsors.
// Health language: describe what happens; never promise outcomes. No donations on this page.
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { PageBanner, SectionHeader, useSettingText } from "../component/common";
import { CheckboxField, CheckboxGroup, FormShell, RadioGroup, SelectField, TextArea, TextField, useForm } from "../component/Form";

const NEIGHBORHOODS = ["Dorchester", "Roxbury", "Mattapan", "Hyde Park", "South End"];
const OFFER_MAX = 600;
const EMAIL = "info@qicodeacademy.org";

// Simple line icons (decorative; each card has a visible heading).
const ICONS = {
  tai_chi_baguazhang: <><circle cx="24" cy="24" r="15" /><path d="M24 9a7.5 7.5 0 0 1 0 15a7.5 7.5 0 0 0 0 15" /><circle cx="24" cy="16.5" r="1.6" /><circle cx="24" cy="31.5" r="1.6" /></>,
  chair_yoga_meditation: <><circle cx="24" cy="11" r="4" /><path d="M24 15v11M14 22l10 4 10-4M15 36c3-5 6-7 9-7s6 2 9 7M11 38h26" /></>,
  massage_acupressure: <><path d="M17 40V22a3 3 0 0 1 6 0v6M23 27v-8a3 3 0 0 1 6 0v8M29 27v-5a3 3 0 0 1 6 0v9c0 6-4 10-10 10h-1c-4 0-7-2-9-6l-3-6a2.6 2.6 0 0 1 4.4-2.7L17 30" /><path d="M8 12c2-2 4-2 6 0M34 9c2-2 4-2 6 0" /></>,
  strength_balance: <><path d="M10 24h28M14 17v14M34 17v14M9 20v8M39 20v8" /><path d="M18 40l6-6 6 6" /></>,
  painting_sewing: <><path d="M10 38c4 0 6-2 6-5s3-4 5-2-1 7-11 7z" /><path d="M20 30L36 10l3 3-16 20" /><path d="M30 34c4-2 7 1 6 4s-5 3-6 0M33 20l7 7" /></>,
  wellness_education: <><path d="M8 13c6-2 11-1 16 3 5-4 10-5 16-3v24c-6-2-11-1-16 3-5-4-10-5-16-3z" /><path d="M24 16v24" /></>,
  food_social: <><path d="M10 22h24v4a10 10 0 0 1-10 10h-4A10 10 0 0 1 10 26z" /><path d="M34 24h3a4 4 0 0 1 0 8h-4M8 40h28" /><path d="M17 16c0-3 2-3 2-6M23 16c0-3 2-3 2-6" /></>,
};

function Icon({ name }) {
  return (
    <svg className="wd-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2.2"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {ICONS[name]}
    </svg>
  );
}

const opts = (map) => Object.entries(map).map(([value, label]) => ({ value, label }));

function InterestForm() {
  const { t } = useTranslation();
  const k = (key) => t(`wellnessDay.interest.${key}`);
  const form = useForm({
    formId: "wd-interest",
    endpoint: "/wellness-day/interest",
    initial: { name: "", email: "", phone: "", neighborhood: "", activities: [], contact_method: "",
      signing_up_for: "", consent_to_contact: false },
    required: ["name"],
    emails: ["email"],
    validate: (v) => ({
      email: !v.email.trim() && !v.phone.trim() ? k("needContact")
        : v.contact_method === "email" && !v.email.trim() ? k("needEmail") : undefined,
      phone: ["phone", "text"].includes(v.contact_method) && !v.phone.trim() ? k("needPhone") : undefined,
      consent_to_contact: v.consent_to_contact ? undefined : k("needConsent"),
    }),
  });
  const labels = { name: k("name"), email: k("email"), phone: k("phone"), neighborhood: k("neighborhood"),
    activities: k("activities"), contact_method: k("contactMethod"), signing_up_for: k("signingUpFor"),
    consent_to_contact: k("consentShort") };
  const activities = t("wellnessDay.offerings", { returnObjects: true }).map((o) => ({ value: o.key, label: o.title }));
  return (
    <FormShell form={form} labels={labels} submitLabel={k("submit")} successTitle={k("successTitle")} className="form-large">
      <p className="alert alert-info">{k("privacy")}</p>
      <TextField form={form} name="name" label={labels.name} required autoComplete="name" />
      <p className="hint wd-contact-hint">{k("contactHint")}</p>
      <TextField form={form} name="email" type="email" label={labels.email} autoComplete="email" />
      <TextField form={form} name="phone" type="tel" label={labels.phone} autoComplete="tel" inputMode="tel"
        hint={t("forms.phoneHint")} />
      <SelectField form={form} name="neighborhood" label={labels.neighborhood} placeholder={k("choose")}
        options={[...NEIGHBORHOODS.map((n) => ({ value: n, label: n })), { value: "Other", label: k("otherNeighborhood") }]} />
      <CheckboxGroup form={form} name="activities" legend={labels.activities} hint={k("activitiesHint")} options={activities} />
      <RadioGroup form={form} name="contact_method" legend={labels.contact_method} options={opts(t("wellnessDay.interest.methods", { returnObjects: true }))} />
      <RadioGroup form={form} name="signing_up_for" legend={labels.signing_up_for} options={opts(t("wellnessDay.interest.forOptions", { returnObjects: true }))} />
      <CheckboxField form={form} name="consent_to_contact" label={k("consent")} required />
    </FormShell>
  );
}

function PartnerForm() {
  const { t } = useTranslation();
  const k = (key, o) => t(`wellnessDay.partner.${key}`, o);
  const o = (key) => opts(t(`wellnessDay.partner.${key}`, { returnObjects: true }));
  const form = useForm({
    formId: "wd-partner",
    endpoint: "/wellness-day/partners",
    initial: { name: "", organization: "", email: "", phone: "", website_or_social: "", participation_types: [],
      offer_description: "", license_type: "", license_number: "", has_insurance: "", compensation: "",
      typical_rate: "", setup_needs: [], availability: [], referral_source: "", agrees_no_sales: false,
      agrees_not_confirmed: false },
    required: ["name", "email", "participation_types", "offer_description"],
    emails: ["email"],
    validate: (v) => {
      const practitioner = v.participation_types.includes("practitioner");
      return {
        offer_description: v.offer_description.length > OFFER_MAX ? k("offerHint") : undefined,
        license_type: practitioner && !v.license_type.trim() ? k("needLicense") : undefined,
        license_number: practitioner && !v.license_number.trim() ? k("needLicense") : undefined,
        agrees_no_sales: v.agrees_no_sales ? undefined : k("needAgree"),
        agrees_not_confirmed: v.agrees_not_confirmed ? undefined : k("needAgree"),
      };
    },
    transform: (v) => ({
      ...v,
      license_type: v.participation_types.includes("practitioner") ? v.license_type : "",
      license_number: v.participation_types.includes("practitioner") ? v.license_number : "",
      typical_rate: v.compensation === "paid" ? v.typical_rate : "",
    }),
  });
  const v = form.values;
  const labels = { name: k("name"), organization: k("organization"), email: k("email"), phone: k("phone"),
    website_or_social: k("link"), participation_types: k("types"), offer_description: k("offer"),
    license_type: k("licenseType"), license_number: k("licenseNumber"), has_insurance: k("insurance"),
    compensation: k("compensation"), typical_rate: k("rate"), setup_needs: k("setup"), availability: k("availability"),
    referral_source: k("referral"), agrees_no_sales: k("agreeNoSalesShort"), agrees_not_confirmed: k("agreeNotConfirmedShort") };
  const left = OFFER_MAX - v.offer_description.length;
  return (
    <FormShell form={form} labels={labels} submitLabel={k("submit")} successTitle={k("successTitle")} className="form-large">
      <div className="grid grid-2 form-pair">
        <TextField form={form} name="name" label={labels.name} required autoComplete="name" />
        <TextField form={form} name="organization" label={labels.organization} autoComplete="organization" />
        <TextField form={form} name="email" type="email" label={labels.email} required autoComplete="email" />
        <TextField form={form} name="phone" type="tel" label={labels.phone} autoComplete="tel" inputMode="tel" />
      </div>
      <TextField form={form} name="website_or_social" label={labels.website_or_social} inputMode="url" autoComplete="url" />
      <CheckboxGroup form={form} name="participation_types" legend={labels.participation_types} hint={k("typesHint")}
        options={o("typeOptions")} required />
      {v.participation_types.includes("practitioner") && (
        <fieldset className="field wd-license">
          <legend>{k("licenseTitle")}</legend>
          <p className="hint">{k("licenseNote")}</p>
          <TextField form={form} name="license_type" label={labels.license_type} hint={k("licenseTypeHint")} required />
          <TextField form={form} name="license_number" label={labels.license_number} required />
        </fieldset>
      )}
      <TextArea form={form} name="offer_description" label={labels.offer_description} required rows={5} maxLength={OFFER_MAX}
        hint={`${k("offerHint")} ${k("charsLeft", { count: left })}`} />
      <RadioGroup form={form} name="has_insurance" legend={labels.has_insurance} options={o("insuranceOptions")} />
      <RadioGroup form={form} name="compensation" legend={labels.compensation} options={o("compensationOptions")} />
      {v.compensation === "paid" && <TextField form={form} name="typical_rate" label={labels.typical_rate} />}
      <CheckboxGroup form={form} name="setup_needs" legend={labels.setup_needs} options={o("setupOptions")} />
      <CheckboxGroup form={form} name="availability" legend={labels.availability} options={o("availabilityOptions")} />
      <TextField form={form} name="referral_source" label={labels.referral_source} />
      <CheckboxField form={form} name="agrees_no_sales" label={k("agreeNoSales")} required />
      <CheckboxField form={form} name="agrees_not_confirmed" label={k("agreeNotConfirmed")} required />
    </FormShell>
  );
}

// Only partners staff marked Confirmed AND "show publicly" (the API enforces both).
function Lineup() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/wellness-day/lineup"), []);
  const items = data ? data.items : [];
  if (!items.length) return null;
  return (
    <section className="section" aria-labelledby="wd-lineup-title">
      <div className="container">
        <SectionHeader title={t("wellnessDay.lineupTitle")} lead={t("wellnessDay.lineupLead")} id="wd-lineup-title" />
        <ul className="wd-lineup">
          {items.map((p, i) => (
            <li key={`${p.name}-${i}`}>
              <strong>{p.name}</strong>
              <span className="muted">{p.participation_types.map((x) => t(`wellnessDay.types.${x}`)).join(" · ")}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default function WellnessDay() {
  const { t } = useTranslation();
  const { actions } = useStore();
  const fromSetting = useSettingText();
  useSeo({ title: t("wellnessDay.title"), description: t("wellnessDay.intro") });
  const status = fromSetting("wellness_day_status", "wellnessDay.statusDefault");
  const date = actions.setting("wellness_day_date").trim();
  const location = actions.setting("wellness_day_location").trim();
  const offerings = t("wellnessDay.offerings", { returnObjects: true });

  return (
    <div className="theme-senior wellness-day">
      <PageBanner motto={t("nav.seniors")} title={t("wellnessDay.title")} lead={t("wellnessDay.lead")}>
        <p className="wd-status"><span className="badge badge-solid">{status}</span></p>
      </PageBanner>

      <section className="section">
        <div className="container container-narrow">
          <p className="page-intro">{t("wellnessDay.intro")}</p>
          <div className="cluster">
            <a className="btn btn-lg" href="#interest">{t("wellnessDay.jumpInterest")}</a>
            <a className="btn btn-lg btn-outline" href="#partners">{t("wellnessDay.jumpPartner")}</a>
          </div>
        </div>
      </section>

      <section className="section section-accent" aria-labelledby="wd-offer-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.offerTitle")} id="wd-offer-title" />
          <ul className="wd-offerings">
            {offerings.map((o) => (
              <li key={o.key} className="feature wd-offering">
                <Icon name={o.key} />
                <div>
                  <h3>{o.title}</h3>
                  <p>{o.body}</p>
                </div>
              </li>
            ))}
          </ul>
          <p className="disclaimer wd-note">{t("wellnessDay.offerNote")}</p>
        </div>
      </section>

      <section className="section">
        <div className="container grid grid-2 wd-details">
          <section className="gain" aria-labelledby="wd-expect-title">
            <h2 id="wd-expect-title">{t("wellnessDay.expectTitle")}</h2>
            <ul className="check-list">{t("wellnessDay.expect", { returnObjects: true }).map((i) => <li key={i}>{i}</li>)}</ul>
          </section>
          <section className="gain" aria-labelledby="wd-when-title">
            <h2 id="wd-when-title">{t("wellnessDay.whenTitle")}</h2>
            {(date || location) && (
              <dl className="level-facts wd-when">
                {date && <div><dt>{t("wellnessDay.dateLabel")}</dt><dd>{date}</dd></div>}
                {location && <div><dt>{t("wellnessDay.locationLabel")}</dt><dd>{location}</dd></div>}
              </dl>
            )}
            {!date && !location && <p style={{ margin: 0 }}>{t("wellnessDay.when")}</p>}
          </section>
        </div>
      </section>

      <Lineup />

      <section className="section section-alt" id="interest" aria-labelledby="wd-interest-title">
        <div className="container container-narrow">
          <h2 id="wd-interest-title">{t("wellnessDay.interest.title")}</h2>
          <p className="lead">{t("wellnessDay.interest.lead")}</p>
          <InterestForm />
        </div>
      </section>

      <section className="section" id="partners" aria-labelledby="wd-partner-title">
        <div className="container container-narrow">
          <h2 id="wd-partner-title">{t("wellnessDay.partner.title")}</h2>
          <p className="lead">{t("wellnessDay.partner.lead")}</p>
          <PartnerForm />
          <p className="wd-questions">
            {t("wellnessDay.partner.questions")}{" "}
            <a href={`mailto:${EMAIL}?subject=${encodeURIComponent("Senior Wellness Day")}`}>{EMAIL}</a>
          </p>
        </div>
      </section>
    </div>
  );
}
