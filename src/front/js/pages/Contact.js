import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { PageBanner } from "../component/common";
import { placeText } from "../component/Cards";
import { FormShell, TextArea, TextField, useForm } from "../component/Form";

function ContactForm() {
  const { t } = useTranslation();
  const form = useForm({
    formId: "contact",
    endpoint: "/contact",
    initial: { name: "", email: "", subject: "", message: "" },
    required: ["name", "email", "message"],
    emails: ["email"],
    transform: (v) => ({ ...v, type: "general" }),
  });
  const labels = { name: t("forms.name"), email: t("forms.email"), subject: t("forms.subject"), message: t("forms.message") };
  return (
    <FormShell form={form} labels={labels} submitLabel={t("contact.submit")}>
      <TextField form={form} name="name" label={labels.name} required autoComplete="name" />
      <TextField form={form} name="email" type="email" label={labels.email} required autoComplete="email" />
      <TextField form={form} name="subject" label={labels.subject} />
      <TextArea form={form} name="message" label={labels.message} required rows={6} maxLength={5000} />
    </FormShell>
  );
}

function Locations() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/programs"), []);
  if (!data) return null;
  // One entry per distinct location, listing the programs held there.
  const map = new Map();
  data.items.forEach((p) => {
    const place = placeText(p.location, p.neighborhood);
    if (!place) return;
    if (!map.has(place)) map.set(place, { place, hood: p.neighborhood, programs: [] });
    map.get(place).programs.push(p.title);
  });
  const list = [...map.values()];
  if (!list.length) return <p className="muted">{t("contact.noLocations")}</p>;
  return (
    <ul className="stack" style={{ listStyle: "none", padding: 0 }}>
      {list.map((l) => (
        <li key={l.place} className="card" style={{ padding: "1rem 1.25rem" }}>
          <strong>{l.place}</strong>
          <p className="muted small" style={{ margin: 0 }}>{l.programs.join(" · ")}</p>
        </li>
      ))}
    </ul>
  );
}

export default function Contact() {
  const { t } = useTranslation();
  const { actions } = useStore();
  useSeo({ title: t("contact.title"), description: t("contact.lead") });
  // Organization contact info comes ONLY from site settings (never personal details).
  const email = actions.setting("org_contact_email");
  const phone = actions.setting("org_contact_phone");

  return (
    <div className="theme-community">
      <PageBanner title={t("contact.title")} lead={t("contact.lead")} />
      <section className="section">
        <div className="container split split-wide-left" style={{ alignItems: "start" }}>
          <section aria-labelledby="contact-form-title">
            <h2 id="contact-form-title">{t("contact.formTitle")}</h2>
            <ContactForm />
          </section>
          <aside className="stack">
            <section className="gain" aria-labelledby="reach-title">
              <h2 id="reach-title" style={{ fontSize: "1.4rem" }}>{t("contact.infoTitle")}</h2>
              {email || phone ? (
                <dl className="event-facts" style={{ marginBottom: 0 }}>
                  {email && (<><dt>{t("forms.email")}</dt><dd><a href={`mailto:${email}`}>{email}</a></dd></>)}
                  {phone && (<><dt>{t("forms.phone")}</dt><dd><a href={`tel:${phone.replace(/[^\d+]/g, "")}`}>{phone}</a></dd></>)}
                </dl>
              ) : (
                <p style={{ margin: 0 }}>{t("contact.noInfo")}</p>
              )}
            </section>
            <section aria-labelledby="map-title">
              <h2 id="map-title" className="sr-only">{t("contact.mapTitle")}</h2>
              <div className="map-placeholder" role="img" aria-label={t("contact.mapPlaceholder")}>
                <svg viewBox="0 0 400 240" aria-hidden="true">
                  <rect width="400" height="240" fill="#e4eef0" />
                  <path d="M0 170 C80 140 120 190 200 160 S330 110 400 140" stroke="#b9cfd4" strokeWidth="18" fill="none" />
                  <path d="M60 0 L110 240 M250 0 L220 240 M0 70 L400 90" stroke="#fff" strokeWidth="8" />
                  <circle cx="200" cy="110" r="14" fill="#a8402b" /><circle cx="200" cy="110" r="5" fill="#fff" />
                </svg>
                <p>{t("contact.mapPlaceholder")}</p>
              </div>
            </section>
          </aside>
        </div>
      </section>
      <section className="section section-alt" aria-labelledby="locations-title">
        <div className="container">
          <h2 id="locations-title">{t("contact.locationsTitle")}</h2>
          <Locations />
        </div>
      </section>
    </div>
  );
}
