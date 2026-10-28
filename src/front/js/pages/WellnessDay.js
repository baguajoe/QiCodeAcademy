// Senior Wellness Day (planned for spring 2027): an event page first, a sign-up page second.
// Hero → a day at a glance → activity cards → marketplace → class photos → details → lineup →
// sign-up tabs (seniors and families | vendors, practitioners and volunteers).
// Health language: describe what happens; never promise outcomes. No donations on this page.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { SectionHeader, useSettingText } from "../component/common";
import { PhotoRow, SiteImage } from "../component/Photo";
import { CheckboxField, CheckboxGroup, FormShell, RadioGroup, SelectField, TextArea, TextField, useForm } from "../component/Form";

const NEIGHBORHOODS = ["Dorchester", "Roxbury", "Mattapan", "Hyde Park", "South End"];
const OFFER_MAX = 600;
const EMAIL = "info@qicodeacademy.org";

// Must match WELLNESS_ACTIVITIES / WELLNESS_PRACTITIONER_TYPES / WELLNESS_VENDOR_TYPES in src/api/models.py.
const ACTIVITIES = ["tai_chi_baguazhang", "chair_yoga_meditation", "chair_massage", "acupuncture", "acupressure",
  "strength_balance", "painting_sewing", "wellness_education", "marketplace", "food_social"];
const PARTICIPATION = ["practitioner_massage", "practitioner_acupuncture", "practitioner_bodywork", "instructor",
  "arts_crafts", "vendor", "food_vendor", "resource_table", "volunteer", "sponsor"];
const PRACTITIONER_TYPES = ["practitioner_massage", "practitioner_acupuncture", "practitioner_bodywork"];
const VENDOR_TYPES = ["vendor", "food_vendor"];
const VENDOR_CATEGORIES = ["crafts", "art", "clothing", "jewelry", "wellness_products", "food", "books_media", "other"];

// Activity cards: our own photos first; stock (credited in credits.json) where we have none yet.
const OFFERINGS = [
  { key: "tai_chi_baguazhang", slot: "research-banner", cat: "movement", position: "center 30%" },
  { key: "chair_yoga_meditation", slot: "wellness-day-yoga", cat: "movement" },
  { key: "strength_balance", slot: "wellness-day-strength", cat: "movement" },
  { key: "chair_massage", slot: "seniors-chair-massage", cat: "care", position: "center 18%" },
  { key: "acupuncture", slot: "wellness-day-acupuncture", cat: "care" },
  { key: "acupressure", slot: "wellness-day-acupressure", cat: "care" },
  { key: "painting_sewing", slot: "wellness-day-crafts", cat: "creativity", position: "center 35%" },
  { key: "marketplace", slot: "wellness-day-marketplace", cat: "creativity" },
  { key: "wellness_education", slot: "wellness-day-education", cat: "community" },
  { key: "food_social", slot: "wellness-day-social", cat: "community" },
];

const DAY = [
  { key: "welcome", slots: ["seniors-join"], position: "center 60%" },
  { key: "choose", slots: ["seniors-chair-massage", "wellness-day-acupuncture", "wellness-day-yoga", "wellness-day-crafts"] },
  { key: "marketplace", slots: ["wellness-day-marketplace"] },
  { key: "lunch", slots: ["wellness-day-social"] },
];

const MARKET_PHOTOS = ["wellness-day-market-baskets", "wellness-day-market-painting", "wellness-day-market-sewing"];
const CLASS_PHOTOS = ["seniors-join", "research-banner", "seniors-baguazhang", "seniors-chair-massage"];

const TABS = ["seniors", "partners"];
const TAB_HASH = { seniors: "signup-seniors", partners: "signup-partners" };
const opts = (map) => Object.entries(map).map(([value, label]) => ({ value, label }));
const hasAny = (list, wanted) => list.some((x) => wanted.includes(x));
const reducedMotion = () => typeof window !== "undefined" && window.matchMedia
  && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function InterestForm({ preset }) {
  const { t } = useTranslation();
  const k = (key) => t(`wellnessDay.interest.${key}`);
  const form = useForm({
    formId: "wd-interest",
    endpoint: "/wellness-day/interest",
    initial: { name: "", email: "", phone: "", neighborhood: "", activities: [], contact_method: "",
      signing_up_for: "", wants_to_sell: false, sell_items: "", needs_table: "", consent_to_contact: false },
    required: ["name"],
    emails: ["email"],
    validate: (v) => ({
      email: !v.email.trim() && !v.phone.trim() ? k("needContact")
        : v.contact_method === "email" && !v.email.trim() ? k("needEmail") : undefined,
      phone: ["phone", "text"].includes(v.contact_method) && !v.phone.trim() ? k("needPhone") : undefined,
      sell_items: v.wants_to_sell && !v.sell_items.trim() ? k("needSellItems") : undefined,
      consent_to_contact: v.consent_to_contact ? undefined : k("needConsent"),
    }),
    transform: (v) => (v.wants_to_sell ? v : { ...v, sell_items: "", needs_table: "" }),
  });
  // "I'm a senior maker" (marketplace band) checks the seller box.
  useEffect(() => {
    if (preset && preset.sell) form.set("wants_to_sell", true);
  }, [preset]); // eslint-disable-line react-hooks/exhaustive-deps

  const v = form.values;
  const labels = { name: k("name"), email: k("email"), phone: k("phone"), neighborhood: k("neighborhood"),
    activities: k("activities"), contact_method: k("contactMethod"), signing_up_for: k("signingUpFor"),
    wants_to_sell: k("wantsToSellShort"), sell_items: k("sellItems"), needs_table: k("needsTable"),
    consent_to_contact: k("consentShort") };
  const activities = ACTIVITIES.map((a) => ({ value: a, label: t(`wellnessDay.interest.activityLabels.${a}`) }));
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
      <fieldset className="field wd-reveal wd-reveal-gold">
        <legend>{k("sellTitle")}</legend>
        <CheckboxField form={form} name="wants_to_sell" label={k("wantsToSell")} />
        {v.wants_to_sell && (
          <>
            <TextField form={form} name="sell_items" label={labels.sell_items} hint={k("sellItemsHint")} required maxLength={300} />
            <RadioGroup form={form} name="needs_table" legend={labels.needs_table} options={opts(t("wellnessDay.interest.yesNo", { returnObjects: true }))} />
          </>
        )}
      </fieldset>
      <CheckboxField form={form} name="consent_to_contact" label={k("consent")} required />
    </FormShell>
  );
}

function PartnerForm({ preset }) {
  const { t } = useTranslation();
  const k = (key, o) => t(`wellnessDay.partner.${key}`, o);
  const o = (key) => opts(t(`wellnessDay.partner.${key}`, { returnObjects: true }));
  const form = useForm({
    formId: "wd-partner",
    endpoint: "/wellness-day/partners",
    initial: { name: "", organization: "", email: "", phone: "", website_or_social: "", participation_types: [],
      offer_description: "", license_type: "", license_number: "", vendor_products: "", vendor_category: "",
      vendor_price_range: "", has_insurance: "", compensation: "", typical_rate: "", setup_needs: [], availability: [],
      referral_source: "", agrees_not_confirmed: false, agrees_respectful: false, agrees_permits: false,
      agrees_restricted_products: false },
    required: ["name", "email", "participation_types", "offer_description"],
    emails: ["email"],
    validate: (v) => {
      const practitioner = hasAny(v.participation_types, PRACTITIONER_TYPES);
      const vendor = hasAny(v.participation_types, VENDOR_TYPES);
      const agree = (f) => (v[f] ? undefined : k("needAgree"));
      return {
        offer_description: v.offer_description.length > OFFER_MAX ? k("offerHint") : undefined,
        license_type: practitioner && !v.license_type.trim() ? k("needLicense") : undefined,
        license_number: practitioner && !v.license_number.trim() ? k("needLicense") : undefined,
        vendor_products: vendor && !v.vendor_products.trim() ? k("needProducts") : undefined,
        agrees_not_confirmed: agree("agrees_not_confirmed"),
        agrees_respectful: agree("agrees_respectful"),
        agrees_permits: agree("agrees_permits"),
        agrees_restricted_products: agree("agrees_restricted_products"),
      };
    },
    transform: (v) => {
      const practitioner = hasAny(v.participation_types, PRACTITIONER_TYPES);
      const vendor = hasAny(v.participation_types, VENDOR_TYPES);
      return {
        ...v,
        license_type: practitioner ? v.license_type : "",
        license_number: practitioner ? v.license_number : "",
        vendor_products: vendor ? v.vendor_products : "",
        vendor_category: vendor ? v.vendor_category : "",
        vendor_price_range: vendor ? v.vendor_price_range : "",
        typical_rate: v.compensation === "paid" ? v.typical_rate : "",
      };
    },
  });
  // "Sell at the marketplace" preselects Vendor.
  useEffect(() => {
    if (preset && preset.type) {
      form.setValues((cur) => (cur.participation_types.includes(preset.type) ? cur
        : { ...cur, participation_types: [...cur.participation_types, preset.type] }));
    }
  }, [preset]); // eslint-disable-line react-hooks/exhaustive-deps

  const v = form.values;
  const practitioner = hasAny(v.participation_types, PRACTITIONER_TYPES);
  const vendor = hasAny(v.participation_types, VENDOR_TYPES);
  const labels = { name: k("name"), organization: k("organization"), email: k("email"), phone: k("phone"),
    website_or_social: k("link"), participation_types: k("types"), offer_description: k("offer"),
    license_type: k("licenseType"), license_number: k("licenseNumber"), vendor_products: k("vendorProducts"),
    vendor_category: k("vendorCategory"), vendor_price_range: k("priceRange"), has_insurance: k("insurance"),
    compensation: k("compensation"), typical_rate: k("rate"), setup_needs: k("setup"), availability: k("availability"),
    referral_source: k("referral"), agrees_not_confirmed: k("agreeNotConfirmedShort"),
    agrees_respectful: k("agreeRespectfulShort"), agrees_permits: k("agreePermitsShort"),
    agrees_restricted_products: k("agreeRestrictedShort") };
  const left = OFFER_MAX - v.offer_description.length;
  const types = PARTICIPATION.map((p) => ({ value: p, label: k(`typeOptions.${p}`) }));
  const categories = VENDOR_CATEGORIES.map((c) => ({ value: c, label: k(`vendorCategories.${c}`) }));
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
        options={types} required />
      {practitioner && (
        <fieldset className="field wd-reveal wd-reveal-clay">
          <legend>{k("licenseTitle")}</legend>
          <p className="hint">{k("licenseNote")}</p>
          <TextField form={form} name="license_type" label={labels.license_type} hint={k("licenseTypeHint")} required />
          <TextField form={form} name="license_number" label={labels.license_number} required />
        </fieldset>
      )}
      {vendor && (
        <fieldset className="field wd-reveal wd-reveal-gold">
          <legend>{k("vendorTitle")}</legend>
          <TextField form={form} name="vendor_products" label={labels.vendor_products} required maxLength={300} />
          <SelectField form={form} name="vendor_category" label={labels.vendor_category}
            placeholder={t("wellnessDay.interest.choose")} options={categories} />
          <TextField form={form} name="vendor_price_range" label={labels.vendor_price_range} hint={k("priceRangeHint")} maxLength={100} />
        </fieldset>
      )}
      <TextArea form={form} name="offer_description" label={labels.offer_description} required rows={5} maxLength={OFFER_MAX}
        hint={`${k("offerHint")} ${k("charsLeft", { count: left })}`} />
      <CheckboxGroup form={form} name="setup_needs" legend={labels.setup_needs} options={o("setupOptions")} />
      <RadioGroup form={form} name="has_insurance" legend={labels.has_insurance} options={o("insuranceOptions")} />
      <RadioGroup form={form} name="compensation" legend={labels.compensation} options={o("compensationOptions")} />
      {v.compensation === "paid" && <TextField form={form} name="typical_rate" label={labels.typical_rate} />}
      <CheckboxGroup form={form} name="availability" legend={labels.availability} options={o("availabilityOptions")} />
      <TextField form={form} name="referral_source" label={labels.referral_source} />
      <fieldset className="field wd-agreements">
        <legend>{k("agreementsTitle")}</legend>
        <CheckboxField form={form} name="agrees_not_confirmed" label={k("agreeNotConfirmed")} required />
        <CheckboxField form={form} name="agrees_respectful" label={k("agreeRespectful")} required />
        <CheckboxField form={form} name="agrees_permits" label={k("agreePermits")} required />
        <CheckboxField form={form} name="agrees_restricted_products" label={k("agreeRestricted")} required />
      </fieldset>
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

// WAI-ARIA tabs: arrow keys / Home / End move between tabs (automatic activation); both
// panels stay mounted so a half-filled form survives a tab switch.
function SignupTabs({ active, onSelect, tabRefs, interestPreset, partnerPreset }) {
  const { t } = useTranslation();
  const label = { seniors: t("wellnessDay.tabSeniors"), partners: t("wellnessDay.tabPartners") };
  const onKeyDown = (e) => {
    const i = TABS.indexOf(active);
    const next = { ArrowRight: i + 1, ArrowDown: i + 1, ArrowLeft: i - 1, ArrowUp: i - 1, Home: 0, End: TABS.length - 1 }[e.key];
    if (next === undefined) return;
    e.preventDefault();
    const tab = TABS[(next + TABS.length) % TABS.length];
    onSelect(tab);
    tabRefs.current[tab].focus();
  };
  return (
    <>
      <div className="wd-tabs" role="tablist" aria-label={t("wellnessDay.tabsLabel")}>
        {TABS.map((tab) => (
          <button key={tab} type="button" role="tab" id={`wd-tab-${tab}`} aria-controls={`wd-panel-${tab}`}
            aria-selected={active === tab} tabIndex={active === tab ? 0 : -1} className={`wd-tab wd-tab-${tab}`}
            ref={(el) => { tabRefs.current[tab] = el; }} onClick={() => onSelect(tab)} onKeyDown={onKeyDown}>
            {label[tab]}
          </button>
        ))}
      </div>
      <div role="tabpanel" id="wd-panel-seniors" aria-labelledby="wd-tab-seniors" tabIndex={0} className="wd-panel"
        hidden={active !== "seniors"}>
        <h3 className="wd-panel-title">{t("wellnessDay.interest.title")}</h3>
        <p className="lead">{t("wellnessDay.interest.lead")}</p>
        <InterestForm preset={interestPreset} />
      </div>
      <div role="tabpanel" id="wd-panel-partners" aria-labelledby="wd-tab-partners" tabIndex={0} className="wd-panel"
        hidden={active !== "partners"}>
        <h3 className="wd-panel-title">{t("wellnessDay.partner.title")}</h3>
        <p className="lead">{t("wellnessDay.partner.lead")}</p>
        <PartnerForm preset={partnerPreset} />
        <p className="wd-questions">
          {t("wellnessDay.partner.questions")}{" "}
          <a href={`mailto:${EMAIL}?subject=${encodeURIComponent("Senior Wellness Day")}`}>{EMAIL}</a>
        </p>
      </div>
    </>
  );
}

export default function WellnessDay() {
  const { t } = useTranslation();
  const { actions } = useStore();
  const fromSetting = useSettingText();
  useSeo({ title: t("wellnessDay.title"), description: t("wellnessDay.intro"), imageSlot: "seniors-banner" });
  const status = fromSetting("wellness_day_status", "wellnessDay.statusDefault");
  const date = actions.setting("wellness_day_date").trim();
  const location = actions.setting("wellness_day_location").trim();

  const [tab, setTab] = useState("seniors");
  const [interestPreset, setInterestPreset] = useState(null);
  const [partnerPreset, setPartnerPreset] = useState(null);
  const signupRef = useRef(null);
  const tabRefs = useRef({});

  // Open a tab (optionally pre-filling the form), scroll to the sign-up section, and focus the tab.
  const openSignup = (which, preset) => (e) => {
    if (e) e.preventDefault();
    setTab(which);
    if (preset && which === "seniors") setInterestPreset({ ...preset, at: Date.now() });
    if (preset && which === "partners") setPartnerPreset({ ...preset, at: Date.now() });
    if (window.history && window.history.replaceState) window.history.replaceState(null, "", `#${TAB_HASH[which]}`);
    requestAnimationFrame(() => {
      if (signupRef.current) signupRef.current.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
      const el = tabRefs.current[which];
      if (el) el.focus({ preventScroll: true });
    });
  };

  // Deep links: #signup-partners / #partners open the partner tab; #signup-seniors / #interest the seniors tab.
  useEffect(() => {
    const fromHash = () => {
      const h = window.location.hash.replace("#", "");
      if (["signup-partners", "partners"].includes(h)) setTab("partners");
      else if (["signup-seniors", "interest"].includes(h)) setTab("seniors");
      else return;
      requestAnimationFrame(() => signupRef.current && signupRef.current.scrollIntoView({ block: "start" }));
    };
    fromHash();
    window.addEventListener("hashchange", fromHash);
    return () => window.removeEventListener("hashchange", fromHash);
  }, []);

  return (
    <div className="theme-senior wellness-day">
      <section className="wd-hero" aria-labelledby="wd-title">
        <div className="wd-hero-media">
          <SiteImage slot="seniors-banner" sizes="100vw" priority ratio={null} position="center 40%" />
        </div>
        <div className="container wd-hero-content">
          <span className="wd-eyebrow">{t("nav.seniors")}</span>
          <h1 id="wd-title">{t("wellnessDay.title")}</h1>
          <p className="wd-status"><span className="wd-status-badge">{status}</span></p>
          <p className="wd-hero-intro">{t("wellnessDay.intro")}</p>
          <div className="wd-hero-actions">
            <a className="btn btn-lg wd-btn-gold" href="#signup-seniors" onClick={openSignup("seniors")}>
              {t("wellnessDay.jumpInterest")}
            </a>
            <a className="btn btn-lg btn-ghost-light" href="#signup-partners" onClick={openSignup("partners")}>
              {t("wellnessDay.jumpPartner")}
            </a>
          </div>
        </div>
      </section>

      <section className="section wd-glance" aria-labelledby="wd-glance-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.glanceTitle")} lead={t("wellnessDay.glanceLead")} id="wd-glance-title" center />
          <ol className="wd-timeline">
            {DAY.map((step, i) => (
              <li key={step.key} className="wd-step">
                <div className={`wd-step-media ${step.slots.length > 1 ? "wd-collage" : ""}`}>
                  {step.slots.map((slot) => (
                    <SiteImage key={slot} slot={slot} ratio="4 / 3"
                      sizes={step.slots.length > 1 ? "(min-width: 64rem) 8rem, 45vw" : "(min-width: 64rem) 17rem, 90vw"}
                      position={step.position} />
                  ))}
                </div>
                <span className="wd-step-marker" aria-hidden="true"><span className="wd-step-num">{i + 1}</span></span>
                <h3><span className="sr-only">{t("wellnessDay.stepLabel", { n: i + 1 })}: </span>{t(`wellnessDay.glance.${step.key}.title`)}</h3>
                <p>{t(`wellnessDay.glance.${step.key}.body`)}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section wd-offer" aria-labelledby="wd-offer-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.offerTitle")} lead={t("wellnessDay.offerLead")} id="wd-offer-title" />
          <ul className="wd-cards">
            {OFFERINGS.map((o) => (
              <li key={o.key} className={`wd-card wd-cat-${o.cat}`}>
                <SiteImage slot={o.slot} ratio="4 / 3" sizes="(min-width: 64rem) 23rem, (min-width: 40rem) 45vw, 100vw"
                  position={o.position} />
                <div className="wd-card-body">
                  <span className="wd-cat">{t(`wellnessDay.categories.${o.cat}`)}</span>
                  <h3>{t(`wellnessDay.offerings.${o.key}.title`)}</h3>
                  <p>{t(`wellnessDay.offerings.${o.key}.body`)}</p>
                </div>
              </li>
            ))}
          </ul>
          <p className="wd-note">{t("wellnessDay.offerNote")}</p>
        </div>
      </section>

      <section className="wd-market" aria-labelledby="wd-market-title">
        <div className="container wd-market-inner">
          <div className="wd-market-text">
            <h2 id="wd-market-title">{t("wellnessDay.marketTitle")}</h2>
            <p>{t("wellnessDay.marketBody")}</p>
            <div className="wd-market-actions">
              <a className="btn btn-lg wd-btn-gold" href="#signup-partners" onClick={openSignup("partners", { type: "vendor" })}>
                {t("wellnessDay.marketSell")}
              </a>
              <a className="btn btn-lg btn-ghost-light" href="#signup-seniors" onClick={openSignup("seniors", { sell: true })}>
                {t("wellnessDay.marketMaker")}
              </a>
            </div>
          </div>
          <div className="wd-market-photos">
            {MARKET_PHOTOS.map((slot) => (
              <SiteImage key={slot} slot={slot} ratio="4 / 3" sizes="(min-width: 64rem) 20rem, 50vw" />
            ))}
          </div>
        </div>
      </section>

      <section className="section wd-photos" aria-labelledby="wd-photos-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.photosTitle")} lead={t("wellnessDay.photosLead")} id="wd-photos-title" />
          <PhotoRow label={t("wellnessDay.photosTitle")}
            items={CLASS_PHOTOS.map((slot) => ({ slot, caption: t(`wellnessDay.photoCaptions.${slot}`) }))} />
        </div>
      </section>

      <section className="section wd-details-band">
        <div className="container grid grid-2 wd-details">
          <section className="wd-panel-card" aria-labelledby="wd-expect-title">
            <h2 id="wd-expect-title">{t("wellnessDay.expectTitle")}</h2>
            <ul className="check-list">{t("wellnessDay.expect", { returnObjects: true }).map((i) => <li key={i}>{i}</li>)}</ul>
          </section>
          <section className="wd-panel-card" aria-labelledby="wd-when-title">
            <h2 id="wd-when-title">{t("wellnessDay.whenTitle")}</h2>
            {(date || location) && (
              <dl className="level-facts wd-when">
                {date && <div><dt>{t("wellnessDay.dateLabel")}</dt><dd>{date}</dd></div>}
                {location && <div><dt>{t("wellnessDay.locationLabel")}</dt><dd>{location}</dd></div>}
              </dl>
            )}
            {!date && !location && <p>{t("wellnessDay.when")}</p>}
          </section>
        </div>
      </section>

      <Lineup />

      <section className="section wd-signup" id="signup" ref={signupRef} aria-labelledby="wd-signup-title">
        <div className="container container-narrow">
          <h2 id="wd-signup-title">{t("wellnessDay.signupTitle")}</h2>
          <p className="lead">{t("wellnessDay.signupLead")}</p>
          <SignupTabs active={tab} onSelect={setTab} tabRefs={tabRefs}
            interestPreset={interestPreset} partnerPreset={partnerPreset} />
        </div>
      </section>
    </div>
  );
}
