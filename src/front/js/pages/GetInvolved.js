import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSeo } from "../seo";
import { PageBanner } from "../component/common";
import { CheckboxGroup, FormShell, TextArea, TextField, useForm } from "../component/Form";

const ROLES = ["coding_mentor", "wellness_assistant", "event_help", "senior_tech_tutor"];

function VolunteerForm() {
  const { t } = useTranslation();
  const form = useForm({
    formId: "volunteer",
    endpoint: "/volunteers",
    initial: { name: "", email: "", phone: "", roles: [], availability: "", message: "" },
    required: ["name", "email", "roles"],
    emails: ["email"],
  });
  const labels = { name: t("forms.fullName"), email: t("forms.email"), phone: t("forms.phone"), roles: t("involved.roles"),
    availability: t("involved.availability"), message: t("forms.message") };
  return (
    <FormShell form={form} labels={labels} submitLabel={t("involved.volunteerSubmit")}>
      <TextField form={form} name="name" label={labels.name} required autoComplete="name" />
      <TextField form={form} name="email" type="email" label={labels.email} required autoComplete="email" />
      <TextField form={form} name="phone" type="tel" label={labels.phone} autoComplete="tel" hint={t("forms.phoneHint")} />
      <CheckboxGroup form={form} name="roles" legend={labels.roles} required
        options={ROLES.map((r) => ({ value: r, label: t(`involved.roleNames.${r}`) }))} />
      <TextArea form={form} name="availability" label={labels.availability} hint={t("involved.availabilityHint")} rows={3} maxLength={2000} />
      <TextArea form={form} name="message" label={labels.message} rows={4} maxLength={5000} />
    </FormShell>
  );
}

// Guest instructor + partner/sponsor inquiries go to POST /api/contact with a type.
function InquiryForm({ type, submitLabel, showOrg }) {
  const { t } = useTranslation();
  const form = useForm({
    formId: `inquiry-${type}`,
    endpoint: "/contact",
    initial: { name: "", email: "", organization: "", subject: "", message: "" },
    required: ["name", "email", "message"],
    emails: ["email"],
    transform: (v) => ({ ...v, type }),
  });
  const labels = { name: t("forms.fullName"), email: t("forms.email"), organization: t("forms.organization"),
    subject: t("forms.subject"), message: t("forms.message") };
  return (
    <FormShell form={form} labels={labels} submitLabel={submitLabel}>
      <TextField form={form} name="name" label={labels.name} required autoComplete="name" />
      <TextField form={form} name="email" type="email" label={labels.email} required autoComplete="email" />
      {showOrg && <TextField form={form} name="organization" label={labels.organization} autoComplete="organization" />}
      <TextField form={form} name="subject" label={labels.subject} />
      <TextArea form={form} name="message" label={labels.message} required maxLength={5000} />
    </FormShell>
  );
}

export default function GetInvolved() {
  const { t } = useTranslation();
  useSeo({ title: t("involved.title"), description: t("involved.lead"), imageSlot: "volunteer-banner" });
  const sections = [
    { id: "volunteer", title: t("involved.volunteerTitle") },
    { id: "guest-instructor", title: t("involved.instructorTitle") },
    { id: "partner", title: t("involved.partnerTitle") },
    { id: "research", title: t("involved.researchTitle") },
  ];
  return (
    <div className="theme-community">
      <PageBanner slot="volunteer-banner" title={t("involved.title")} lead={t("involved.lead")} />
      <section className="section">
        <div className="container">
          <nav aria-labelledby="jump-title" className="jump-nav">
            <h2 id="jump-title" className="eyebrow" style={{ fontFamily: "var(--font-body)", fontSize: "0.85rem" }}>{t("involved.jump")}</h2>
            <ul className="cluster" style={{ listStyle: "none", padding: 0 }}>
              {sections.map((s) => <li key={s.id}><a className="btn btn-outline btn-sm" href={`#${s.id}`}>{s.title}</a></li>)}
            </ul>
          </nav>

          <div className="involved-grid">
            <section id="volunteer" aria-labelledby="volunteer-title" className="panel">
              <h2 id="volunteer-title">{t("involved.volunteerTitle")}</h2>
              <p>{t("involved.volunteerLead")}</p>
              <VolunteerForm />
            </section>

            <section id="guest-instructor" aria-labelledby="gi-title" className="panel theme-senior">
              <h2 id="gi-title">{t("involved.instructorTitle")}</h2>
              <p>{t("involved.instructorLead")}</p>
              <InquiryForm type="guest_instructor" submitLabel={t("involved.instructorSubmit")} />
            </section>

            <section id="partner" aria-labelledby="partner-title" className="panel theme-youth">
              <h2 id="partner-title">{t("involved.partnerTitle")}</h2>
              <p>{t("involved.partnerLead")}</p>
              <InquiryForm type="partner" showOrg submitLabel={t("involved.partnerSubmit")} />
            </section>

            <section id="research" aria-labelledby="research-link-title" className="panel theme-research">
              <h2 id="research-link-title">{t("involved.researchTitle")}</h2>
              <p>{t("involved.researchLead")}</p>
              <Link className="btn" to="/research#partner-inquiry">{t("involved.researchCta")}</Link>
              <hr />
              <h3>{t("home.donateTitle")}</h3>
              <p>{t("home.donateBody")}</p>
              <Link className="btn btn-donate" to="/donate">{t("home.donateCta")}</Link>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}
