import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { PageBanner, SectionHeader } from "../component/common";
import { Photo, SiteImage } from "../component/Photo";
import { CredentialsList, FounderCard, PressStrip, useFounder } from "../component/Founder";
import { Neighborhoods } from "./Home";

function TeamCard({ member }) {
  return (
    <article className="card team-card">
      <Photo src={member.photo_url} alt={member.photo_url ? `Photo of ${member.name}` : ""}
        sizes="(min-width: 48rem) 20rem, 100vw"
        placeholder={{ division: "community", subject: `Headshot: ${member.name}`, size: "800×1000" }} />
      <div className="card-body">
        <h4 style={{ marginBottom: 0 }}>{member.name}</h4>
        {member.role_title && <p className="role">{member.role_title}</p>}
        {member.bio && <p>{member.bio}</p>}
      </div>
    </article>
  );
}

// The founder's instructor profile: portrait, role, credentials, link to full bio.
function FounderInstructorCard({ founder }) {
  const { t } = useTranslation();
  return (
    <article className="card team-card team-card-wide theme-senior">
      <SiteImage slot="founder-portrait" sizes="(min-width: 48rem) 16rem, 100vw" ratio={null} />
      <div className="card-body">
        <h4 style={{ marginBottom: 0 }}>{founder.name}</h4>
        <p className="role">{founder.role}</p>
        <h5 className="small" style={{ margin: "0.5rem 0" }}>{t("founder.credentialsTitle")}</h5>
        <CredentialsList items={founder.credentials} compact />
        <Link className="more-link" to="/about/founder">{t("about.readMoreFounder")}</Link>
      </div>
    </article>
  );
}

function TeamGroup({ title, members, extra, emptyText, id }) {
  if (!members.length && !extra && !emptyText) return null;
  return (
    <section aria-labelledby={id} style={{ marginBottom: "2.5rem" }}>
      <h3 id={id}>{title}</h3>
      {members.length || extra ? (
        <div className="team-grid">
          {extra}
          {members.map((m) => <TeamCard key={m.id} member={m} />)}
        </div>
      ) : (
        <p className="muted">{emptyText}</p>
      )}
    </section>
  );
}

export default function About() {
  const { t } = useTranslation();
  const { data } = useApi(() => api.get("/team"), []);
  const team = data ? data.items : [];
  const founder = useFounder(team);
  const others = team.filter((m) => m !== founder.member);
  const byGroup = (g) => others.filter((m) => m.group === g);
  const mission = t("about.mission", { returnObjects: true });
  useSeo({ title: t("nav.about"), description: mission[0], imageSlot: "about-banner" });

  return (
    <div className="theme-community">
      <PageBanner slot="about-banner" title={t("about.title")} lead={t("about.lead")} />

      <section className="section" aria-labelledby="mission-title">
        <div className="container split split-wide-left" style={{ alignItems: "start" }}>
          <div className="prose">
            <h2 id="mission-title">{t("about.missionTitle")}</h2>
            {mission.map((p, i) => <p key={i} className={i === 0 ? "page-intro" : ""}>{p}</p>)}
          </div>
          <aside className="gain theme-community" aria-labelledby="vision-title">
            <h2 id="vision-title">{t("about.visionTitle")}</h2>
            <p style={{ fontSize: "1.2rem", fontFamily: "var(--font-heading)" }}>{t("about.vision")}</p>
          </aside>
        </div>
      </section>

      <section className="section section-alt" aria-labelledby="founder-title">
        <div className="container">
          <SectionHeader title={t("about.founderTitle")} id="founder-title" />
          <FounderCard founder={founder} />
          <div style={{ marginTop: "1.5rem" }}><PressStrip /></div>
        </div>
      </section>

      <section className="section" aria-labelledby="team-title">
        <div className="container">
          <SectionHeader title={t("about.teamTitle")} id="team-title" />
          <TeamGroup id="board-title" title={t("about.boardTitle")} members={byGroup("board")} emptyText={t("about.boardEmpty")} />
          <TeamGroup id="instructors-title" title={t("about.instructorsTitle")} members={byGroup("instructor")}
            extra={<FounderInstructorCard founder={founder} />} />
          <TeamGroup id="staff-title" title={t("about.staffTitle")} members={byGroup("staff")} />
          <TeamGroup id="advisors-title" title={t("about.advisorsTitle")} members={byGroup("advisor")} />
        </div>
      </section>

      <Neighborhoods />
    </div>
  );
}
