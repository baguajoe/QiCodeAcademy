// Division program pages: Youth, Seniors, Intergenerational.
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSeo } from "../seo";
import { PageBanner, SectionHeader, WellnessDisclaimer } from "../component/common";
import { ProgramList, ProgramSection } from "../component/ProgramList";
import { FeatureGrid, ModuleCard, ScheduleTable, StatusBadge, WeeklyProjects, useCurriculum } from "../component/Curriculum";
import { SessionFlowDiagram, StepsDiagram } from "../component/Diagrams";

function FocusList({ items }) {
  return <ul className="tag-list">{items.map((i) => <li key={i}>{i}</li>)}</ul>;
}

// Level 1 in full; Levels 2–4 as short "in development" cards. All from /api/curriculum.
function YouthCurriculum() {
  const { t } = useTranslation();
  const { modules } = useCurriculum("youth");
  if (!modules.length) return null;
  const [first, ...rest] = modules;
  const facts = [
    first.age_range && [t("youth.facts.ages"), first.age_range],
    first.duration && [t("youth.facts.format"), first.duration],
  ].filter(Boolean);
  return (
    <>
      <section className="section" aria-labelledby="level1-title">
        <div className="container">
          <div className="level-one">
            <div>
              <span className="eyebrow">{t("youth.levelOneEyebrow")}</span>
              <div className="cluster" style={{ gap: "0.5rem", marginBottom: "0.5rem" }}><StatusBadge module={first} /></div>
              <h2 id="level1-title">{first.title}</h2>
              {first.summary && <p className="page-intro">{first.summary}</p>}
              {facts.length > 0 && (
                <dl className="level-facts">
                  {facts.map(([k, v]) => (<div key={k}><dt>{k}</dt><dd>{v}</dd></div>))}
                </dl>
              )}
              {first.format_notes && first.format_notes.length > 0 && (
                <ul className="fact-chips">{first.format_notes.map((f) => <li key={f}>{f}</li>)}</ul>
              )}
            </div>
            {first.projects && first.projects.length > 0 && (
              <div>
                <h3>{t("youth.weeklyTitle")}</h3>
                <WeeklyProjects projects={first.projects} weekLabel={(n) => t("youth.week", { n })} />
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="section section-accent" aria-labelledby="session-title">
        <div className="container split" style={{ alignItems: "start" }}>
          <div>
            <SectionHeader title={t("youth.sessionTitle")} lead={t("youth.sessionLead")} id="session-title" />
          </div>
          <ScheduleTable caption={t("youth.sessionTitle")} rows={t("youth.session", { returnObjects: true })} />
        </div>
      </section>

      <section className="section" aria-labelledby="features-title">
        <div className="container">
          <SectionHeader title={t("youth.featuresTitle")} id="features-title" />
          <FeatureGrid items={t("youth.features", { returnObjects: true })} />
        </div>
      </section>

      {rest.length > 0 && (
        <section className="section section-alt" aria-labelledby="levels-title">
          <div className="container">
            <SectionHeader title={t("youth.moreLevelsTitle")} lead={t("youth.moreLevelsLead")} id="levels-title" />
            <div className="grid grid-3">{rest.map((m) => <ModuleCard key={m.id} module={m} />)}</div>
          </div>
        </section>
      )}
    </>
  );
}

export function YouthPrograms() {
  const { t } = useTranslation();
  useSeo({ title: t("youth.title"), description: `${t("youth.intro")} ${t("youth.ageNote")}`, imageSlot: "youth-banner" });
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
          <p className="center muted" style={{ marginTop: "1rem" }}>{t("youth.ageNote")}</p>
        </div>
      </section>
      <YouthCurriculum />
      <ProgramSection division="youth" title={t("youth.programsTitle")} lead={t("youth.guardianNote")} id="youth-programs-title" />
      <section className="section">
        <div className="container">
          <Link className="more-link" to="/programs/intergenerational">{t("home.interCta")}</Link>
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
