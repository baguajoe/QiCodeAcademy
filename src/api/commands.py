"""CLI commands: `flask seed`, `flask remove-samples`, `flask create-admin`."""
import os
from datetime import date, datetime, timedelta

import click
from sqlalchemy import select

from .extensions import db
from .founder_content import (FOUNDER_CREDENTIALS, FOUNDER_FULL_BIO, FOUNDER_NAME, FOUNDER_ROLE,
                              FOUNDER_SHORT_BIO, LEGACY_FINGERPRINTS, fingerprint)
from .models import CurriculumModule, Event, ResearchReference, ImpactStat, Program, SiteImage, SiteSetting, TeamMember, User

SAMPLE = "[SAMPLE]"

# Where classes are taught (names only — never street addresses).
TEACHING_LOCATIONS = "\n".join([
    "Grove Hall Senior Center",
    "Parkway Community YMCA (West Roxbury)",
    "Codman Square Library",
    "Boston City Parks",
])
# Earlier seeded defaults, replaced by `flask seed` only if staff haven't edited them.
LEGACY_TEACHING_LOCATIONS = {"Grove Hall Senior Center\nCodman Square Library\nBoston City Parks"}

DEFAULT_SETTINGS = [
    # key, value, is_public
    ("tax_status", "Qi Code Academy, Inc. has applied for 501(c)(3) tax-exempt status. "
                   "Please consult your tax advisor regarding deductibility.", True),
    ("research_status", "In development — no active studies.", True),
    ("social_facebook", "", True),
    ("social_instagram", "", True),
    ("social_youtube", "", True),
    # Founder page content (editable in the admin; see founder_content.py)
    ("founder_full_bio", FOUNDER_FULL_BIO, True),
    ("founder_credentials", FOUNDER_CREDENTIALS, True),
    # "As featured in" links — outlet names show as plain text until a URL is filled in
    ("press_globe_url", "", True),
    ("press_wcvb_url", "", True),
    # Where classes are taught — names only, one per line, NO street addresses (Contact page)
    ("teaching_locations", TEACHING_LOCATIONS, True),
    # Organization contact info shown on Contact page/footer (blank = hidden)
    ("org_contact_email", "", True),
    ("org_contact_phone", "", True),
]

# Keep in sync with SLOTS in src/front/js/siteImages.js and IMAGE_GUIDE.md.
SITE_IMAGE_SLOTS = [
    "hero-home", "home-card-youth", "home-card-seniors", "home-card-research",
    "about-banner", "founder-portrait", "founder-teaching",
    "youth-banner", "seniors-banner", "intergenerational-banner", "research-banner",
    "events-banner", "volunteer-banner", "donate",
]


def _next_weekday(start, weekday):
    return start + timedelta(days=(weekday - start.weekday()) % 7 or 7)


def sample_programs(today):
    return [
        dict(division="youth", title=f"{SAMPLE} Intro to Python for Teens",
             description="A beginner-friendly 8-week course where teens build small games and "
                         "tools in Python, with short movement breaks to stay focused.",
             age_range="Ages 14–18", neighborhood="Dorchester",
             location="Dorchester Branch Library (sample location)",
             schedule="Saturdays, 10:00 AM – 12:00 PM",
             start_date=today + timedelta(days=21), end_date=today + timedelta(days=77),
             capacity=16, cost="Free"),
        dict(division="youth", title=f"{SAMPLE} Web Design Club",
             description="Teens learn HTML, CSS, and design basics by building a "
                         "personal website they can share with family.",
             age_range="Ages 14–18", neighborhood="Roxbury",
             location="Roxbury community center (sample location)",
             schedule="Wednesdays, 3:30 PM – 5:00 PM",
             start_date=today + timedelta(days=14), end_date=today + timedelta(days=70),
             capacity=12, cost="Free"),
        dict(division="senior", title=f"{SAMPLE} Gentle Qigong for Balance",
             description="Slow, seated-or-standing qigong movement sessions focused on balance, "
                         "breathing, and relaxation. All experience levels welcome.",
             age_range="60+", neighborhood="Chinatown",
             location="Chinatown community room (sample location)",
             schedule="Tuesdays & Thursdays, 9:30 – 10:30 AM",
             start_date=today + timedelta(days=10), end_date=today + timedelta(days=66),
             capacity=20, cost="Free"),
        dict(division="senior", title=f"{SAMPLE} Smartphone & Tablet Basics",
             description="Small-group, patient help with video calls, photos, messaging, and "
                         "staying safe online.",
             age_range="60+", neighborhood="Jamaica Plain",
             location="Jamaica Plain senior center (sample location)",
             schedule="Mondays, 1:00 – 2:30 PM",
             start_date=today + timedelta(days=17), end_date=today + timedelta(days=45),
             capacity=10, cost="Free"),
        dict(division="intergenerational", title=f"{SAMPLE} Tech & Tea: Teens Teach Tech",
             description="Teens and older adults pair up: teens share tech skills, elders share "
                         "stories and wisdom, and everyone shares tea.",
             age_range="Teens 13–18 and adults 60+", neighborhood="Mattapan",
             location="Mattapan community space (sample location)",
             schedule="Every other Sunday, 2:00 – 4:00 PM",
             start_date=today + timedelta(days=28), end_date=today + timedelta(days=112),
             capacity=24, cost="Free"),
    ]


def sample_events(today):
    sat = _next_weekday(today, 5)
    def at(d, h, m=0):
        return datetime(d.year, d.month, d.day, h, m)
    return [
        dict(division="community", title=f"{SAMPLE} Open House & Program Preview",
             description="Meet instructors, try a mini coding lesson and a short qigong session, "
                         "and learn about upcoming programs.",
             neighborhood="Dorchester", location="Sample venue, Dorchester",
             start_datetime=at(sat + timedelta(days=7), 11), end_datetime=at(sat + timedelta(days=7), 13)),
        dict(division="youth", title=f"{SAMPLE} Youth Hack Afternoon",
             description="A relaxed, beginner-friendly afternoon of building small projects in teams.",
             neighborhood="Roxbury", location="Sample venue, Roxbury",
             start_datetime=at(sat + timedelta(days=14), 13), end_datetime=at(sat + timedelta(days=14), 17)),
        dict(division="senior", title=f"{SAMPLE} Qigong in the Park",
             description="A free outdoor qigong session for older adults. Chairs available.",
             neighborhood="Jamaica Plain", location="Sample park location, Jamaica Plain",
             start_datetime=at(sat + timedelta(days=21), 9, 30), end_datetime=at(sat + timedelta(days=21), 10, 30)),
        dict(division="intergenerational", title=f"{SAMPLE} Family Tech Help Day",
             description="Bring a device and a question — teen volunteers and staff help family "
                         "members of all ages.",
             neighborhood="Mattapan", location="Sample venue, Mattapan",
             start_datetime=at(sat + timedelta(days=28), 10), end_datetime=at(sat + timedelta(days=28), 12)),
        dict(division="community", title=f"{SAMPLE} Community Kickoff (past event)",
             description="Our first community gathering.",
             neighborhood="Dorchester", location="Sample venue, Dorchester",
             start_datetime=at(today - timedelta(days=30), 17), end_datetime=at(today - timedelta(days=30), 19)),
    ]




def seed_settings():
    added = 0
    for key, value, is_public in DEFAULT_SETTINGS:
        if not db.session.scalar(select(SiteSetting).where(SiteSetting.key == key)):
            db.session.add(SiteSetting(key=key, value=value, is_public=is_public))
            added += 1
    for slot in SITE_IMAGE_SLOTS:
        if not db.session.scalar(select(SiteImage).where(SiteImage.slot_key == slot)):
            db.session.add(SiteImage(slot_key=slot, image_url="", alt_text=""))
    return added


# ---------------------------------------------------------------------------
# Curriculum (real program content — seeded once, editable in the admin)
# ---------------------------------------------------------------------------
YOUTH_LEVEL_1_PROJECTS = [
    "Guess the Number — variables, input and output, conditionals, loops, reading error messages",
    "Rock-Paper-Scissors — functions, randomization, branching logic",
    "Trivia Battle — lists, dictionaries, scoring systems",
    "Pong — introduction to Pygame: coordinates, game loops, keyboard input, collision",
    "Snake — continuous movement, game state, spawning objects",
    "Space Shooter — sprites, projectiles, sound, health systems",
    "Mini Fighting Game — object-oriented programming, character state, animation, hit detection",
    "Racing / Dodge — timers, difficulty progression, game balancing",
    "Intelligent Enemies — algorithms, state machines, decision logic, agent behavior",
    "Introduction to AI & Games — AI literacy, how Python powers modern AI, responsible use",
    "Original Game Project — design documents, teamwork, project management",
    "Finish, Portfolio & Demo Day — debugging, version control, portfolios, presenting your work",
]

CURRICULUM_SEED = [
    dict(division="youth", sort_order=1, title="Level 1 — Python & Game Development",
         age_range="Ages 14–18", duration="12 weeks · 2 sessions a week · 90 minutes each",
         summary="Students learn Python by building games — writing code on the first day and playing what they "
                 "wrote before they leave. Each week adds a new project, ending with an original game students "
                 "design themselves and present at a public Demo Day.",
         format_notes=["Free for families", "Up to 15 students", "No coding experience needed"],
         projects=YOUTH_LEVEL_1_PROJECTS, status="in_development", launch_label="Launching 2027"),
    # Levels 2–4: title + one-sentence summary only (summaries drafted; see DECISIONS.md).
    dict(division="youth", sort_order=2, title="Level 2 — Web & Application Development",
         summary="Students build websites and apps, learning how the software they use every day is made.",
         status="in_development"),
    dict(division="youth", sort_order=3, title="Level 3 — Intelligent Applications",
         summary="Students build applications that use data and AI, and learn to use these tools responsibly.",
         status="in_development"),
    dict(division="youth", sort_order=4, title="Level 4 — Advanced Projects, Entrepreneurship & Career Preparation",
         summary="Students lead advanced projects, explore entrepreneurship, and prepare portfolios for college "
                 "and careers.",
         status="in_development"),
    # Seniors: describe what happens in class only — no promised health outcomes.
    dict(division="senior", sort_order=1, title="Traditional Yang-Style Tai Chi",
         summary="Relaxed, flowing movement with controlled stepping, coordinated breathing, and good body "
                 "alignment, taught in the lineage of Vincent Chu and Gin Soon Chu.",
         learning_goals=["Standing exercises", "Ba Duan Jin–inspired movements", "Weight shifting and posture work",
                         "A 22-movement medium-frame form, adapted for accessibility by removing the two "
                         "Snake Creeps Down sections"],
         projects=["Foundations", "Sections of the form", "The complete form", "Ongoing refinement"],
         status="available"),
    dict(division="senior", sort_order=2, title="Traditional Baguazhang",
         summary="Circle walking, changes of direction, and coordinated palm movements: a practice of balance and "
                 "coordination while moving.",
         learning_goals=["Standing and stepping", "Circle walking", "Palm positions", "Controlled changes of direction"],
         adaptations="Large circles, slow steps, comfortable postures, and support as needed. Faster movement is "
                     "optional and only when a participant is ready.",
         projects=["Standing and stepping", "Circle walking and palm positions", "Directional changes",
                   "Additional palm changes"],
         status="available"),
    # One-sentence plain descriptions (drafted; see DECISIONS.md).
    dict(division="senior", sort_order=3, title="Yoga & Gentle Stretching",
         summary="Gentle yoga poses and stretches, done standing or seated, at a pace that feels comfortable.",
         status="available"),
    dict(division="senior", sort_order=4, title="Chair-Based Movement",
         summary="Seated and chair-supported versions of our movement practice, so everyone can take part.",
         status="available"),
    dict(division="senior", sort_order=5, title="Breathing & Meditation",
         summary="Simple breathing exercises and quiet, guided meditation, often used to open or close class.",
         status="available"),
]


def seed_curriculum():
    """Add any seeded curriculum module that doesn't exist yet (matched by division + title).
    Never overwrites staff edits."""
    added = 0
    for mod in CURRICULUM_SEED:
        exists = db.session.scalar(select(CurriculumModule).where(
            CurriculumModule.division == mod["division"], CurriculumModule.title == mod["title"]))
        if not exists:
            db.session.add(CurriculumModule(**{"format_notes": [], "learning_goals": [], "projects": [], **mod},
                                            is_published=True))
            added += 1
    return added


# Background research to be checked by Joseph. Seeded UNVERIFIED with empty URLs, so
# they stay hidden on the public site until someone adds the link and marks them verified.
RESEARCH_REFERENCES_SEED = [
    dict(title="Exercise for preventing falls in older people living in the community",
         authors="Sherrington C, Fairhall NJ, Wallbank GK, et al.",
         publication="Cochrane Database of Systematic Reviews", year=2019,
         summary="Across 7 studies and 2,655 participants, Tai Chi may reduce the rate of falls by about 19% "
                 "(low-certainty evidence)."),
    dict(title="Tai Chi for fall prevention and balance improvement in older adults: a systematic review and "
               "meta-analysis of randomized controlled trials",
         authors="Chen W, Li M, Li H, Lin Y, Feng Z.", publication="Frontiers in Public Health", year=2023),
    dict(title="Systematic review and meta-analysis: Tai Chi for preventing falls in older adults",
         authors="Huang Z-G, Feng Y-H, Li Y-H, Lv C-S.", publication="BMJ Open, 7(2):e013661", year=2017),
]


def seed_research_references():
    added = 0
    for ref in RESEARCH_REFERENCES_SEED:
        if not db.session.scalar(select(ResearchReference).where(ResearchReference.title == ref["title"])):
            db.session.add(ResearchReference(**ref, url=None, is_verified=False))
            added += 1
    return added


def upgrade_founder_text():
    """Replace earlier seeded founder text with the current version — only where staff
    haven't edited it (matched by fingerprint). Returns the number of fields updated."""
    n = 0
    member = db.session.scalar(select(TeamMember).where(TeamMember.name == FOUNDER_NAME))
    if member and fingerprint(member.bio) in LEGACY_FINGERPRINTS["short_bio"]:
        member.bio = FOUNDER_SHORT_BIO
        n += 1
    row = db.session.scalar(select(SiteSetting).where(SiteSetting.key == "teaching_locations"))
    if row and row.value in LEGACY_TEACHING_LOCATIONS:
        row.value = TEACHING_LOCATIONS
        n += 1
    for key, current, kind in (("founder_full_bio", FOUNDER_FULL_BIO, "full_bio"),
                               ("founder_credentials", FOUNDER_CREDENTIALS, "credentials")):
        row = db.session.scalar(select(SiteSetting).where(SiteSetting.key == key))
        if row and fingerprint(row.value) in LEGACY_FINGERPRINTS[kind]:
            row.value = current
            n += 1
    return n


def seed_founder():
    """Add the founder as a TeamMember once (editable afterwards in the admin)."""
    if db.session.scalar(select(TeamMember).where(TeamMember.name == FOUNDER_NAME)):
        return False
    db.session.add(TeamMember(name=FOUNDER_NAME, role_title=FOUNDER_ROLE, bio=FOUNDER_SHORT_BIO,
                              group="staff", sort_order=0))
    return True


def seed_admin(email, password, name="Administrator"):
    email = (email or "").strip().lower()
    if not email or not password:
        return None, "ADMIN_EMAIL / ADMIN_PASSWORD not set — skipped admin user."
    user = db.session.scalar(select(User).where(User.email == email))
    if user:
        return user, f"Admin {email} already exists (password unchanged)."
    if len(password) < 10:
        return None, "ADMIN_PASSWORD must be at least 10 characters — skipped admin user."
    user = User(email=email, name=name, is_active=True)
    user.set_password(password)
    db.session.add(user)
    return user, f"Created admin {email}."


def register_commands(app):
    @app.cli.command("seed")
    @click.option("--with-samples", is_flag=True,
                  help="LOCAL DEV ONLY: also add [SAMPLE] programs and events for testing layouts.")
    @click.option("--no-samples", is_flag=True, hidden=True, help="Deprecated no-op (samples are off by default).")
    def seed(with_samples, no_samples):
        """Seed admin user, site settings, photo slots, founder, curriculum, research refs (idempotent).

        No impact stats or other made-up numbers are ever seeded. [SAMPLE] programs/events
        are only added with --with-samples, for local layout testing."""
        _, msg = seed_admin(os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD"),
                            os.getenv("ADMIN_NAME", "Administrator"))
        click.echo(msg)
        click.echo(f"Settings added: {seed_settings()}")
        if seed_founder():
            click.echo("Added founder team member.")
        if (n := seed_curriculum()):
            click.echo(f"Added {n} curriculum module(s).")
        if (n := seed_research_references()):
            click.echo(f"Added {n} research reference(s) — unverified and hidden until checked in the admin.")
        if (n := upgrade_founder_text()):
            click.echo(f"Updated {n} founder/location field(s) to the current version.")

        if with_samples and not no_samples:
            today = date.today()
            if not db.session.scalar(select(Program).where(Program.title.startswith(SAMPLE))):
                for p in sample_programs(today):
                    db.session.add(Program(**p, is_active=True))
                click.echo("Added sample programs (local dev only).")
            if not db.session.scalar(select(Event).where(Event.title.startswith(SAMPLE))):
                for e in sample_events(today):
                    db.session.add(Event(**e, is_published=True))
                click.echo("Added sample events (local dev only).")
        db.session.commit()
        click.echo("Seed complete.")

    @app.cli.command("remove-samples")
    def remove_samples():
        """Delete every [SAMPLE] program/event/impact stat (programs with registrations are kept)."""
        n = 0
        for model, col in ((Program, Program.title), (Event, Event.title), (ImpactStat, ImpactStat.label)):
            for obj in db.session.scalars(select(model).where(col.startswith(SAMPLE))):
                if isinstance(obj, Program) and obj.registrations:
                    click.echo(f"Kept (has registrations): {obj.title}")
                    continue
                db.session.delete(obj)
                n += 1
        db.session.commit()
        click.echo(f"Removed {n} sample records.")

    @app.cli.command("create-admin")
    @click.argument("email")
    @click.option("--name", default="Administrator")
    @click.password_option()
    def create_admin(email, name, password):
        """Create an additional admin user."""
        user, msg = seed_admin(email, password, name)
        db.session.commit()
        click.echo(msg)
