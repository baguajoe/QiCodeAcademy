// Senior Wellness Day (May 2027): an event page first, a sign-up page second.
// Hero → event basics → how the day works (seven areas) → mind, body & movement cards → bodywork and
// creative cards → marketplace → resources and refreshments → details → lineup → sign-up tabs.
// Health language: describe what happens ("may support", never promises). No donations or budget figures.
// Photos: our own first, credited stock in allowed slots, else a line icon. Each photo appears once.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { SectionHeader, useSettingText } from "../component/common";
import { SiteImage } from "../component/Photo";
import { resolveSlot } from "../siteImages";
import { CheckboxField, CheckboxGroup, FormShell, RadioGroup, SelectField, TextArea, TextField, useForm } from "../component/Form";

const NEIGHBORHOODS = ["Dorchester", "Roxbury", "Mattapan", "Hyde Park", "South End"];
const OFFER_MAX = 600;
const EMAIL = "info@qicodeacademy.org";

// Must match WELLNESS_ACTIVITIES / WELLNESS_PRACTITIONER_TYPES / WELLNESS_VENDOR_TYPES in src/api/models.py.
const ACTIVITIES = ["tai_chi_baguazhang", "chair_yoga_meditation", "chair_hip_hop", "fall_prevention_balance",
  "self_massage", "sound_healing", "chair_massage", "acupuncture", "painting", "marketplace", "resources", "food_social"];
const PARTICIPATION = ["practitioner_massage", "practitioner_acupuncture", "practitioner_bodywork", "sound_healing",
  "instructor_chair_yoga", "instructor_chair_hip_hop", "instructor_meditation", "instructor", "painting", "vendor",
  "food_vendor", "resource_table", "volunteer", "sponsor"];
const PRACTITIONER_TYPES = ["practitioner_massage", "practitioner_acupuncture", "practitioner_bodywork"];
const VENDOR_TYPES = ["vendor", "food_vendor"];
const VENDOR_CATEGORIES = ["visual_art", "jewelry", "baskets", "clothing", "quilts_textiles", "pottery", "greeting_cards",
  "books", "skincare_wellness", "sea_moss", "food", "insurance_financial", "other"];

// Line icons (24×24, stroked) for cards with no photo yet and for the seven areas.
const ICONS = {
  movement: "M12 3a9 9 0 1 0 0 18 4.5 4.5 0 0 1 0-9 4.5 4.5 0 0 0 0-9Zm0 4.5a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4Zm0 9a1.2 1.2 0 1 1 0 2.4 1.2 1.2 0 0 1 0-2.4Z",
  heart: "M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z",
  palette: "M12 3a9 9 0 0 0 0 18c1.2 0 1.8-.8 1.8-1.8 0-1.2-1-1.5-1-2.6 0-1 .8-1.6 1.8-1.6H17a4 4 0 0 0 4-4C21 6.6 17 3 12 3ZM7.5 11.5h.01M10 7.5h.01M15 7.5h.01",
  bowl: "M3 12h18a9 9 0 0 1-18 0ZM8 21h8M16 4.5c1.2 1.2 1.2 3 0 4.2M19 2.5c2.3 2.3 2.3 6 0 8.3",
  market: "M4 9h16l-1.2-4H5.2L4 9Zm0 0v1.5a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0V9M5.5 13v7h13v-7M10 20v-4h4v4",
  info: "M3 11h18M5 11v9M19 11v9M8 11V4h8v7M10.5 6.5h3M10.5 8.5h3",
  cup: "M4 8h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V8ZM16 10h1.5a2.5 2.5 0 0 1 0 5H16M7 3.5v2M11 3.5v2",
  balance: "M12 3.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM5 10l7-1.5 7 1.5M12 8.5v6l-3 6.5M12 14.5l4.5 2.5",
  hand: "M8 11V5.5a1.5 1.5 0 0 1 3 0V10m0-5.5V4a1.5 1.5 0 0 1 3 0v6m0-4.5a1.5 1.5 0 0 1 3 0V12m0-3a1.5 1.5 0 0 1 3 0v4a8 8 0 0 1-8 8h-.5a6.5 6.5 0 0 1-5.4-2.9L4.3 15a1.5 1.5 0 0 1 2.5-1.7L8 15",
  leaf: "M5 19c0-8 6-14 15-14 0 9-6 15-14 15H5Zm0 0 8-8",
  people: "M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm7 0a2.5 2.5 0 1 0 0-5M3.5 20a5.5 5.5 0 0 1 11 0M16 14a4.5 4.5 0 0 1 4.5 6",
};

function LineIcon({ name, size = 24 }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden="true" focusable="false">
      <path d={ICONS[name]} fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// A card's photo, or (when the slot has no photo yet) a line icon in the same 4:3 frame.
function CardMedia({ slot, icon, position, sizes }) {
  const { store } = useStore();
  if (resolveSlot(slot, store.siteImages).kind === "placeholder") {
    return <div className="wd-card-icon"><LineIcon name={icon} size={56} /></div>;
  }
  return <SiteImage slot={slot} ratio="4 / 3" sizes={sizes} position={position} />;
}

const CARD_SIZES = "(min-width: 64rem) 23rem, (min-width: 40rem) 45vw, 100vw";

// Our own photos first (Tai Chi, Baguazhang, Qigong, chair massage; fall prevention takes our own photo
// only, an icon until we have one); stock (credited in credits.json) or an icon for the rest.
const MOVEMENT = [
  { key: "tai_chi", slot: "seniors-join", icon: "movement", position: "center 45%" },
  { key: "baguazhang", slot: "research-banner", icon: "movement" },
  { key: "qigong", slot: "seniors-baguazhang", icon: "movement", position: "center 30%" },
  { key: "chair_yoga", slot: "wellness-day-chair-yoga", icon: "movement" },
  { key: "chair_hip_hop", slot: "wellness-day-chair-hip-hop", icon: "movement", position: "center 20%" },
  { key: "meditation_breathing", slot: "wellness-day-breathing", icon: "movement" },
  { key: "fall_prevention_balance", slot: "wellness-day-balance", icon: "balance" },
  { key: "self_massage", slot: "wellness-day-self-massage", icon: "hand" },
  { key: "sound_healing", slot: "wellness-day-sound", icon: "bowl" },
].map((o) => ({ ...o, cat: "movement" }));
const SERVICES = [
  { key: "chair_massage", slot: "seniors-chair-massage", icon: "heart", cat: "care", position: "center 18%" },
  { key: "acupuncture", slot: "wellness-day-acupuncture", icon: "heart", cat: "care", untimed: true },
  { key: "painting", slot: "wellness-day-painting", icon: "palette", cat: "creativity" },
];
const COMMUNITY = [
  { key: "resources", slot: "wellness-day-resources", icon: "info", cat: "community" },
  { key: "refreshments", slot: "wellness-day-social", icon: "cup", cat: "community" },
];

// How the day works: seven areas open at the same time.
const AREAS = [
  { key: "main", icon: "movement" }, { key: "bodywork", icon: "heart" }, { key: "creative", icon: "palette" },
  { key: "sound", icon: "bowl" }, { key: "marketplace", icon: "market" }, { key: "resources", icon: "info" },
  { key: "refreshments", icon: "cup" },
];

// What we hope the day brings (same order as wellnessDay.hopes).
const HOPE_ICONS = ["movement", "people", "info", "market"];

// Marketplace strip: art and crafts, jewelry, natural products (icon until we have a photo).
const MARKET_PHOTOS = [
  { slot: "wellness-day-market-baskets", icon: "market" },
  { slot: "wellness-day-market-jewelry", icon: "market" },
  { slot: "wellness-day-market-natural", icon: "leaf", label: "marketNatural" },
];

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

// A grid of activity cards: photo (or icon), category, title, length, description.
function Cards({ items }) {
  const { t } = useTranslation();
  return (
    <ul className="wd-cards">
      {items.map((o) => {
        const meta = t(`wellnessDay.offerings.${o.key}.duration`);
        return (
          <li key={o.key} className={`wd-card wd-cat-${o.cat}`}>
            <CardMedia slot={o.slot} icon={o.icon} position={o.position} sizes={CARD_SIZES} />
            <div className="wd-card-body">
              <span className="wd-cat">{t(`wellnessDay.categories.${o.cat}`)}</span>
              <h3>{t(`wellnessDay.offerings.${o.key}.title`)}</h3>
              {meta && (
                <p className="wd-duration">
                  {!o.untimed && (
                    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">
                      <circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" strokeWidth="2" />
                      <path d="M12 7.5V12l3 2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  )}
                  {!o.untimed && <span className="sr-only">{t("wellnessDay.durationLabel")}: </span>}
                  {meta}
                </p>
              )}
              <p>{t(`wellnessDay.offerings.${o.key}.body`)}</p>
            </div>
          </li>
        );
      })}
    </ul>
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
  const { store, actions } = useStore();
  const fromSetting = useSettingText();
  useSeo({ title: t("wellnessDay.title"), description: t("wellnessDay.intro"), imageSlot: "seniors-banner" });
  const status = fromSetting("wellness_day_status", "wellnessDay.statusDefault");
  const date = actions.setting("wellness_day_date").trim() || t("wellnessDay.basics.whenDefault");
  const location = actions.setting("wellness_day_location").trim() || t("wellnessDay.basics.whereDefault");

  const isPlaceholder = (slot) => resolveSlot(slot, store.siteImages).kind === "placeholder";

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

      <section className="section wd-mission" aria-labelledby="wd-why-title">
        <div className="container wd-mission-inner">
          <div className="wd-why">
            <h2 id="wd-why-title">{t("wellnessDay.whyTitle")}</h2>
            <p>{t("wellnessDay.whyBody")}</p>
          </div>
          <div>
            <h3 className="wd-hopes-title">{t("wellnessDay.hopesTitle")}</h3>
            <ul className="wd-hopes">
              {t("wellnessDay.hopes", { returnObjects: true }).map((h, i) => (
                <li key={h}><span className="wd-area-icon"><LineIcon name={HOPE_ICONS[i]} /></span>{h}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="wd-basics" aria-labelledby="wd-basics-title">
        <div className="container">
          <h2 id="wd-basics-title" className="sr-only">{t("wellnessDay.basicsTitle")}</h2>
          <dl className="wd-facts">
            <div><dt>{t("wellnessDay.basics.whenLabel")}</dt><dd>{date}<br />{t("wellnessDay.basics.time")}</dd></div>
            <div><dt>{t("wellnessDay.basics.whereLabel")}</dt><dd>{location}</dd></div>
            <div><dt>{t("wellnessDay.basics.costLabel")}</dt><dd>{t("wellnessDay.basics.cost")}</dd></div>
            <div><dt>{t("wellnessDay.basics.whoLabel")}</dt><dd>{t("wellnessDay.basics.who")}</dd></div>
          </dl>
        </div>
      </section>

      <section className="section wd-areas-band" aria-labelledby="wd-areas-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.areasTitle")} lead={t("wellnessDay.areasLead")} id="wd-areas-title" center />
          <ul className="wd-areas">
            {AREAS.map((a) => (
              <li key={a.key} className={`wd-area wd-area-${a.key}`}>
                <span className="wd-area-icon"><LineIcon name={a.icon} size={30} /></span>
                <h3>{t(`wellnessDay.areas.${a.key}.title`)}</h3>
                <p>{t(`wellnessDay.areas.${a.key}.body`)}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section wd-offer" aria-labelledby="wd-offer-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.movementTitle")} lead={t("wellnessDay.movementLead")} id="wd-offer-title" />
          <Cards items={MOVEMENT} />
        </div>
      </section>

      <section className="section wd-services" aria-labelledby="wd-services-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.servicesTitle")} lead={t("wellnessDay.servicesLead")} id="wd-services-title" />
          <Cards items={SERVICES} />
        </div>
      </section>

      <section className="wd-market" aria-labelledby="wd-market-title">
        <div className="container">
          <div className="wd-market-head">
            <h2 id="wd-market-title">{t("wellnessDay.marketTitle")}</h2>
            <p className="wd-market-hours">{t("wellnessDay.marketHours")}</p>
            <p>{t("wellnessDay.marketBody")}</p>
          </div>
          <ul className="wd-market-strip" aria-label={t("wellnessDay.marketPhotosLabel")}>
            {MARKET_PHOTOS.map((m) => (
              <li key={m.slot}>
                <CardMedia slot={m.slot} icon={m.icon} sizes="(min-width: 64rem) 22rem, 33vw" />
                {m.label && isPlaceholder(m.slot) && <span className="wd-strip-label">{t(`wellnessDay.${m.label}`)}</span>}
              </li>
            ))}
          </ul>
          <div className="wd-market-inner">
            <div>
              <h3>{t("wellnessDay.marketVendorsTitle")}</h3>
              <ul className="wd-vendors">
                {t("wellnessDay.marketVendors", { returnObjects: true }).map((v) => <li key={v}>{v}</li>)}
              </ul>
            </div>
            <div>
              <ul className="wd-market-rules">
                {t("wellnessDay.marketRules", { returnObjects: true }).map((r) => <li key={r}>{r}</li>)}
              </ul>
              <div className="wd-market-actions">
                <a className="btn btn-lg wd-btn-gold" href="#signup-partners" onClick={openSignup("partners", { type: "vendor" })}>
                  {t("wellnessDay.marketSell")}
                </a>
                <a className="btn btn-lg btn-ghost-light" href="#signup-seniors" onClick={openSignup("seniors", { sell: true })}>
                  {t("wellnessDay.marketMaker")}
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section wd-community" aria-labelledby="wd-community-title">
        <div className="container">
          <SectionHeader title={t("wellnessDay.communityTitle")} lead={t("wellnessDay.communityLead")} id="wd-community-title" />
          <Cards items={COMMUNITY} />
        </div>
      </section>

      <section className="section wd-details-band">
        <div className="container grid grid-2 wd-details">
          <section className="wd-panel-card" aria-labelledby="wd-expect-title">
            <h2 id="wd-expect-title">{t("wellnessDay.expectTitle")}</h2>
            <ul className="check-list">{t("wellnessDay.expect", { returnObjects: true }).map((i) => <li key={i}>{i}</li>)}</ul>
          </section>
          <section className="wd-panel-card" aria-labelledby="wd-good-title">
            <h2 id="wd-good-title">{t("wellnessDay.goodTitle")}</h2>
            <ul className="check-list">{t("wellnessDay.good", { returnObjects: true }).map((i) => <li key={i}>{i}</li>)}</ul>
          </section>
        </div>
      </section>

      <Lineup />

      <section className="wd-about" aria-labelledby="wd-about-title">
        <div className="container wd-about-inner">
          <div>
            <h2 id="wd-about-title">{t("wellnessDay.aboutTitle")}</h2>
            <p>{t("wellnessDay.aboutBody")}</p>
          </div>
          <Link className="btn btn-lg" to="/about">{t("wellnessDay.aboutLink")}</Link>
        </div>
      </section>

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
