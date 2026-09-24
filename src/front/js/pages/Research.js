import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";
import { Empty, PageBanner, SectionHeader } from "../component/common";
import { NewsCard } from "../component/Cards";
import { PartnershipDiagram, StepsDiagram } from "../component/Diagrams";
import { FormShell, TextArea, TextField, useForm } from "../component/Form";

function References() {
  const { t } = useTranslation();
  const { data, loading } = useApi(() => api.get("/research/references"), []);
  if (loading) return null;
  const items = data ? data.items : [];
  if (!items.length) return <Empty>{t("research.referencesEmpty")}</Empty>;
  return (
    <ol className="stack" style={{ paddingLeft: "1.2em" }}>
      {items.map((r) => (
        <li key={r.id}>
          <p style={{ margin: 0 }}>
            <strong>{r.url ? <a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}<span className="sr-only"> ({t("common.opensNewTab")})</span></a> : r.title}</strong>
            {r.authors && <> — {r.authors}</>}
            {r.year && <> ({r.year})</>}
          </p>
          {r.summary && <p className="muted" style={{ margin: 0 }}>{r.summary}</p>}
        </li>
      ))}
    </ol>
  );
}

function ResearchNews() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/news", { params: { category: "research", per_page: 3 } }), []);
  if (!data) return null;
  if (!data.items.length) return <p className="muted">{t("research.noNews")}</p>;
  return <div className="grid grid-3">{data.items.map((p) => <NewsCard key={p.id} post={p} />)}</div>;
}

function PartnerInquiryForm() {
  const { t } = useTranslation();
  const form = useForm({
    formId: "research-inquiry",
    endpoint: "/research/inquiries",
    initial: { name: "", institution: "", role: "", email: "", area_of_interest: "", message: "" },
    required: ["name", "institution", "email"],
    emails: ["email"],
  });
  const labels = { name: t("forms.fullName"), institution: t("research.form.institution"), role: t("research.form.role"),
    email: t("forms.email"), area_of_interest: t("research.form.area"), message: t("forms.message") };
  return (
    <FormShell form={form} labels={labels} submitLabel={t("research.form.sendInquiry")}>
      <div className="grid grid-2" style={{ gap: "0 1.5rem" }}>
        <TextField form={form} name="name" label={labels.name} required autoComplete="name" />
        <TextField form={form} name="email" type="email" label={labels.email} required autoComplete="email" />
        <TextField form={form} name="institution" label={labels.institution} required autoComplete="organization" />
        <TextField form={form} name="role" label={labels.role} autoComplete="organization-title" />
      </div>
      <TextField form={form} name="area_of_interest" label={labels.area_of_interest} />
      <TextArea form={form} name="message" label={labels.message} maxLength={5000} />
    </FormShell>
  );
}

function NotifyForm() {
  const { t } = useTranslation();
  const form = useForm({
    formId: "research-notify",
    endpoint: "/research/interest",
    initial: { name: "", email_or_phone: "", neighborhood: "", consent_to_contact: true },
    required: ["name", "email_or_phone"],
  });
  const labels = { name: t("forms.name"), email_or_phone: t("research.form.emailOrPhone"), neighborhood: t("common.neighborhood") };
  return (
    <FormShell form={form} labels={labels} submitLabel={t("research.form.notifyMe")}>
      <p className="alert alert-info"><strong>{t("research.notifyNote")}</strong></p>
      <TextField form={form} name="name" label={labels.name} required autoComplete="name" />
      <TextField form={form} name="email_or_phone" label={labels.email_or_phone} required
        hint={t("research.form.emailOrPhoneHint")} />
      <TextField form={form} name="neighborhood" label={labels.neighborhood} list="research-hoods" autoComplete="address-level3" />
      <datalist id="research-hoods">
        {t("neighborhoods.list", { returnObjects: true }).map((n) => <option key={n} value={n} />)}
      </datalist>
    </FormShell>
  );
}

export default function Research() {
  const { t } = useTranslation();
  const { actions } = useStore();
  useSeo({ title: t("research.title"), description: t("research.vision"), imageSlot: "research-banner" });
  const status = actions.setting("research_status", "In development — no active studies.");

  return (
    <div className="theme-research">
      <PageBanner slot="research-banner" motto={t("divisions.research.motto")} title={t("research.title")} lead={t("research.lead")} />

      <section className="section" aria-labelledby="rvision-title">
        <div className="container split split-wide-left" style={{ alignItems: "start" }}>
          <div className="prose">
            <h2 id="rvision-title">{t("research.visionTitle")}</h2>
            <p className="page-intro">{t("research.vision")}</p>
            <p className="muted">{t("research.visionNote")}</p>
          </div>
          <aside className="status-box" aria-labelledby="rstatus-title">
            <h2 id="rstatus-title" className="eyebrow" style={{ fontFamily: "var(--font-body)", fontSize: "0.85rem" }}>{t("research.statusTitle")}</h2>
            <p className="status">{status}</p>
          </aside>
        </div>
      </section>

      <section className="section section-accent" aria-labelledby="partnership-title">
        <div className="container">
          <SectionHeader title={t("research.partnershipTitle")} lead={t("research.partnershipLead")} id="partnership-title" />
          <PartnershipDiagram title={t("research.partnershipTitle")} centerLabel={t("research.studyCenter")}
            leftTitle={t("research.qcaBringsTitle")} left={t("research.qcaBrings", { returnObjects: true })}
            rightTitle={t("research.partnersBringTitle")} right={t("research.partnersBring", { returnObjects: true })} />
        </div>
      </section>

      <section className="section" aria-labelledby="roadmap-title">
        <div className="container">
          <SectionHeader title={t("research.roadmapTitle")} lead={t("research.roadmapLead")} id="roadmap-title" />
          <StepsDiagram division="research" title={t("research.roadmapTitle")} steps={t("research.roadmap", { returnObjects: true })} />
        </div>
      </section>

      <section className="section section-alt" aria-labelledby="refs-title">
        <div className="container">
          <SectionHeader title={t("research.referencesTitle")} lead={t("research.referencesLead")} id="refs-title" />
          <References />
        </div>
      </section>

      <section className="section" aria-labelledby="rnews-title">
        <div className="container">
          <SectionHeader title={t("research.newsTitle")} id="rnews-title" />
          <ResearchNews />
        </div>
      </section>

      <section className="section section-accent">
        <div className="container grid grid-2" style={{ alignItems: "start", gap: "3rem" }}>
          <div id="partner-inquiry" aria-labelledby="inquiry-title" role="region">
            <h2 id="inquiry-title">{t("research.inquiryTitle")}</h2>
            <p>{t("research.inquiryLead")}</p>
            <PartnerInquiryForm />
          </div>
          <div id="notify" aria-labelledby="notify-title" role="region">
            <h2 id="notify-title">{t("research.notifyTitle")}</h2>
            <p>{t("research.notifyLead")}</p>
            <NotifyForm />
          </div>
        </div>
      </section>
    </div>
  );
}
