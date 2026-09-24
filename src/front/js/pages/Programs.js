// Division program pages: Youth, Seniors, Intergenerational.
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSeo } from "../seo";
import { PageBanner, SectionHeader, WellnessDisclaimer } from "../component/common";
import { ProgramList } from "../component/ProgramList";
import { SessionFlowDiagram, StepsDiagram } from "../component/Diagrams";

function FocusList({ items }) {
  return <ul className="tag-list">{items.map((i) => <li key={i}>{i}</li>)}</ul>;
}

export function YouthPrograms() {
  const { t } = useTranslation();
  useSeo({ title: t("youth.title"), description: t("youth.intro"), imageSlot: "youth-banner" });
  return (
    <div className="theme-youth">
      <PageBanner slot="youth-banner" motto={t("divisions.youth.motto")} title={t("youth.title")} lead={t("youth.lead")} />
      <section className="section">
        <div className="container">
          <div className="prose">
            <h2>{t("youth.introTitle")}</h2>
            <p className="page-intro">{t("youth.intro")}</p>
            <h3>{t("youth.focusTitle")}</h3>
          </div>
          <FocusList items={t("youth.focus", { returnObjects: true })} />
        </div>
      </section>
      <section className="section section-accent" aria-labelledby="pathway-title">
        <div className="container">
          <SectionHeader title={t("youth.pathwayTitle")} lead={t("youth.pathwayLead")} id="pathway-title" />
          <StepsDiagram division="youth" motif="grid" title={t("youth.pathwayTitle")}
            startNote={t("youth.pathwayStart")} steps={t("youth.pathway", { returnObjects: true })} />
        </div>
      </section>
      <section className="section" aria-labelledby="youth-programs-title">
        <div className="container">
          <SectionHeader title={t("youth.programsTitle")} lead={t("youth.guardianNote")} id="youth-programs-title" />
          <ProgramList division="youth" emptyText={t("youth.noPrograms")} />
          <p style={{ marginTop: "2rem" }}>
            <Link className="more-link" to="/programs/intergenerational">{t("home.interCta")}</Link>
          </p>
        </div>
      </section>
    </div>
  );
}

export function SeniorPrograms() {
  const { t } = useTranslation();
  useSeo({ title: t("seniors.title"), description: t("seniors.intro"), imageSlot: "seniors-banner" });
  return (
    <div className="theme-senior">
      <PageBanner slot="seniors-banner" motto={t("divisions.senior.motto")} title={t("seniors.title")} lead={t("seniors.lead")} />
      <section className="section">
        <div className="container">
          <div className="prose">
            <h2>{t("seniors.introTitle")}</h2>
            <p className="page-intro">{t("seniors.intro")}</p>
            <h3>{t("seniors.focusTitle")}</h3>
          </div>
          <FocusList items={t("seniors.focus", { returnObjects: true })} />
        </div>
      </section>
      <section className="section section-accent" aria-labelledby="flow-title">
        <div className="container">
          <SectionHeader title={t("seniors.flowTitle")} lead={t("seniors.flowLead")} id="flow-title" />
          <SessionFlowDiagram title={t("seniors.flowTitle")} centerLabel={t("seniors.flowCenter")}
            steps={t("seniors.flow", { returnObjects: true })} />
        </div>
      </section>
      <section className="section" aria-labelledby="senior-programs-title">
        <div className="container">
          <SectionHeader title={t("seniors.programsTitle")} id="senior-programs-title" />
          <ProgramList division="senior" emptyText={t("seniors.noPrograms")} />
          <div style={{ marginTop: "2rem" }}><WellnessDisclaimer /></div>
        </div>
      </section>
    </div>
  );
}

export function IntergenerationalPrograms() {
  const { t } = useTranslation();
  useSeo({ title: t("inter.title"), description: t("inter.intro"), imageSlot: "intergenerational-banner" });
  return (
    <div className="theme-intergenerational">
      <PageBanner slot="intergenerational-banner" motto={t("divisions.intergenerational.motto")} title={t("inter.title")} lead={t("inter.lead")} />
      <section className="section">
        <div className="container">
          <div className="prose">
            <h2>{t("inter.introTitle")}</h2>
            <p className="page-intro">{t("inter.intro")}</p>
          </div>
          <div className="two-gains">
            <div className="gain theme-youth">
              <h3>{t("inter.youthGainTitle")}</h3>
              <p>{t("inter.youthGain")}</p>
            </div>
            <div className="gain theme-senior">
              <h3>{t("inter.seniorGainTitle")}</h3>
              <p>{t("inter.seniorGain")}</p>
            </div>
          </div>
        </div>
      </section>
      <section className="section section-accent" aria-labelledby="inter-programs-title">
        <div className="container">
          <SectionHeader title={t("inter.programsTitle")} id="inter-programs-title" />
          <ProgramList division="intergenerational" emptyText={t("inter.noPrograms")} />
          <div style={{ marginTop: "2rem" }}><WellnessDisclaimer /></div>
        </div>
      </section>
    </div>
  );
}
