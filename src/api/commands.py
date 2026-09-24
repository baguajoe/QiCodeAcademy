"""CLI commands: `flask seed`, `flask remove-samples`, `flask create-admin`."""
import os
from datetime import date, datetime, timedelta

import click
from sqlalchemy import select

from .extensions import db
from .founder_content import (FOUNDER_CREDENTIALS, FOUNDER_FULL_BIO, FOUNDER_NAME, FOUNDER_ROLE,
                              FOUNDER_SHORT_BIO, LEGACY_FINGERPRINTS, fingerprint)
from .models import Event, ImpactStat, Program, SiteImage, SiteSetting, TeamMember, User

SAMPLE = "[SAMPLE]"

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
    ("teaching_locations", "Grove Hall Senior Center\nCodman Square Library\nBoston City Parks", True),
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


def upgrade_founder_text():
    """Replace earlier seeded founder text with the current version — only where staff
    haven't edited it (matched by fingerprint). Returns the number of fields updated."""
    n = 0
    member = db.session.scalar(select(TeamMember).where(TeamMember.name == FOUNDER_NAME))
    if member and fingerprint(member.bio) in LEGACY_FINGERPRINTS["short_bio"]:
        member.bio = FOUNDER_SHORT_BIO
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
        if (n := upgrade_founder_text()):
            click.echo(f"Updated {n} founder text field(s) to the current version.")

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
