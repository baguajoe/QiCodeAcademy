"""SQLAlchemy models for Qi Code Academy.

Conventions
- Timestamps (created_at/updated_at/published_at) are stored as naive UTC.
- Event start/end datetimes are stored as naive *Boston wall-clock* time
  (America/New_York) because every event is local; see DECISIONS.md.
- Enum-like columns are plain strings validated in schemas.py (portable
  migrations, no Postgres ENUM types to alter later).
- NO health, medical, or diagnostic fields exist on any model, by design.
"""
import re
import unicodedata
from datetime import datetime, timezone

from sqlalchemy import event, func, select
from sqlalchemy.orm import Session, validates
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .sanitize import sanitize_html

# ---------------------------------------------------------------------------
# Choice lists (shared with schemas and Flask-Admin)
# ---------------------------------------------------------------------------
PROGRAM_DIVISIONS = ("youth", "senior", "intergenerational")
EVENT_DIVISIONS = ("youth", "senior", "intergenerational", "research", "community")
GALLERY_DIVISIONS = EVENT_DIVISIONS
REGISTRATION_TYPES = ("youth", "senior")
REGISTRATION_STATUSES = ("pending", "confirmed", "waitlist", "cancelled")
SEAT_HOLDING_STATUSES = ("pending", "confirmed")
VOLUNTEER_ROLES = ("coding_mentor", "wellness_assistant", "event_help", "senior_tech_tutor")
CONTACT_TYPES = ("general", "guest_instructor", "partner")
DONATION_DESIGNATIONS = ("youth", "senior", "research", "general")
DONATION_STATUSES = ("pending", "completed", "failed", "expired", "refunded")
NEWS_CATEGORIES = ("youth", "seniors", "research", "community")
TEAM_GROUPS = ("board", "staff", "instructor", "advisor")
PARTNER_TYPES = ("sponsor", "community", "research")
CURRICULUM_DIVISIONS = ("youth", "senior", "research")
CURRICULUM_STATUSES = ("available", "in_development")

# Which program divisions accept which registration type.
REGISTRATION_TYPE_DIVISIONS = {
    "youth": ("youth", "intergenerational"),
    "senior": ("senior", "intergenerational"),
}


class ModelRuleError(ValueError):
    """Raised when a write would violate a business rule enforced at the model layer."""


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def slugify(text, max_length=180):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:max_length].strip("-") or "item"


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Admin user
# ---------------------------------------------------------------------------
class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False, default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime)

    @validates("email")
    def _normalize_email(self, key, value):
        return (value or "").strip().lower()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def __str__(self):
        return self.email


# ---------------------------------------------------------------------------
# Programs & events
# ---------------------------------------------------------------------------
class Program(TimestampMixin, db.Model):
    __tablename__ = "programs"
    __sluggable__ = True
    id = db.Column(db.Integer, primary_key=True)
    division = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False, default="")
    age_range = db.Column(db.String(100))
    neighborhood = db.Column(db.String(100), index=True)
    location = db.Column(db.String(255))
    schedule = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    capacity = db.Column(db.Integer)  # NULL = unlimited
    cost = db.Column(db.String(100))  # display text, e.g. "Free" or "$20 sliding scale"
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    image_url = db.Column(db.String(500))
    image_alt = db.Column(db.String(300))

    registrations = db.relationship("Registration", back_populates="program", lazy="select")

    @property
    def seats_taken(self):
        if self.id is None:
            return 0
        return db.session.scalar(
            select(func.count(Registration.id)).where(
                Registration.program_id == self.id,
                Registration.status.in_(SEAT_HOLDING_STATUSES),
            )
        ) or 0

    @property
    def seats_left(self):
        if self.capacity is None:
            return None
        return max(self.capacity - self.seats_taken, 0)

    @property
    def is_full(self):
        return self.capacity is not None and self.seats_left == 0

    def __str__(self):
        return self.title


class Event(TimestampMixin, db.Model):
    __tablename__ = "events"
    __sluggable__ = True
    id = db.Column(db.Integer, primary_key=True)
    division = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False, default="")
    neighborhood = db.Column(db.String(100), index=True)
    location = db.Column(db.String(255))
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)  # Boston local time
    end_datetime = db.Column(db.DateTime)                               # Boston local time
    image_url = db.Column(db.String(500))
    image_alt = db.Column(db.String(300))
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Registrations
# ---------------------------------------------------------------------------
class Registration(TimestampMixin, db.Model):
    """Program registration.

    RULE: a youth participant's own email/phone are never stored — only the
    guardian's. Enforced in the schema *and* in a before_flush hook below.
    """
    __tablename__ = "registrations"
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    type = db.Column(db.String(10), nullable=False, index=True)  # youth | senior
    # Guardian (youth only)
    guardian_name = db.Column(db.String(120))
    guardian_email = db.Column(db.String(255))
    guardian_phone = db.Column(db.String(40))
    # Participant
    participant_first_name = db.Column(db.String(80), nullable=False)
    participant_last_name = db.Column(db.String(80), nullable=False)
    grade = db.Column(db.String(20))           # youth only
    email = db.Column(db.String(255))          # senior only
    phone = db.Column(db.String(40))           # senior only
    emergency_contact_name = db.Column(db.String(120), nullable=False)
    emergency_contact_phone = db.Column(db.String(40), nullable=False)
    photo_consent = db.Column(db.Boolean, nullable=False, default=False)
    guardian_consent = db.Column(db.Boolean)   # youth only
    comfort_notes = db.Column(db.Text)         # senior only, optional free text
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    admin_notes = db.Column(db.Text)

    program = db.relationship("Program", back_populates="registrations")

    @property
    def participant_name(self):
        return f"{self.participant_first_name} {self.participant_last_name}".strip()

    @property
    def contact_email(self):
        """Where confirmations go: the guardian for youth, the participant for seniors."""
        return self.guardian_email if self.type == "youth" else self.email


# ---------------------------------------------------------------------------
# Inbound forms
# ---------------------------------------------------------------------------
class Volunteer(TimestampMixin, db.Model):
    __tablename__ = "volunteers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(40))
    roles = db.Column(db.JSON, nullable=False, default=list)
    availability = db.Column(db.Text)
    message = db.Column(db.Text)


class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False, default="general", index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(200))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)


# ---------------------------------------------------------------------------
# Donations
# ---------------------------------------------------------------------------
class Donation(TimestampMixin, db.Model):
    __tablename__ = "donations"
    id = db.Column(db.Integer, primary_key=True)
    stripe_session_id = db.Column(db.String(255), unique=True, index=True)
    stripe_payment_intent_id = db.Column(db.String(255), index=True)
    stripe_subscription_id = db.Column(db.String(255), index=True)
    stripe_invoice_id = db.Column(db.String(255), unique=True)
    stripe_customer_id = db.Column(db.String(255))
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="usd")
    recurring = db.Column(db.Boolean, nullable=False, default=False)
    designation = db.Column(db.String(20), nullable=False, default="general", index=True)
    donor_name = db.Column(db.String(120))
    donor_email = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    subscription_status = db.Column(db.String(30))  # recurring only: active | canceled | ...
    receipt_sent_at = db.Column(db.DateTime)


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
class NewsPost(TimestampMixin, db.Model):
    __tablename__ = "news_posts"
    __sluggable__ = True
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    body = db.Column(db.Text, nullable=False, default="")
    cover_image_url = db.Column(db.String(500))
    cover_image_alt = db.Column(db.String(300))
    category = db.Column(db.String(20), nullable=False, default="community", index=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)
    published_at = db.Column(db.DateTime, index=True)

    @validates("body")
    def _sanitize_body(self, key, value):
        # Runs on every assignment (API, Flask-Admin, seed) so stored HTML is always clean.
        return sanitize_html(value or "")

    def __str__(self):
        return self.title


class TeamMember(TimestampMixin, db.Model):
    __tablename__ = "team_members"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role_title = db.Column(db.String(150))
    bio = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    group = db.Column(db.String(20), nullable=False, default="staff", index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def __str__(self):
        return self.name


class Partner(TimestampMixin, db.Model):
    __tablename__ = "partners"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="community", index=True)
    logo_url = db.Column(db.String(500))
    website_url = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def __str__(self):
        return self.name


class ImpactStat(TimestampMixin, db.Model):
    __tablename__ = "impact_stats"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(150), nullable=False)
    value = db.Column(db.String(50), nullable=False)  # display text, e.g. "120+"
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class SiteSetting(TimestampMixin, db.Model):
    __tablename__ = "site_settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False, default="")
    is_public = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.key


class SiteImage(TimestampMixin, db.Model):
    __tablename__ = "site_images"
    id = db.Column(db.Integer, primary_key=True)
    slot_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    image_url = db.Column(db.String(500), nullable=False, default="")
    alt_text = db.Column(db.String(300), nullable=False, default="")

    def __str__(self):
        return self.slot_key


class GalleryPhoto(TimestampMixin, db.Model):
    """Cannot be published unless consent_confirmed is true (enforced on flush)."""
    __tablename__ = "gallery_photos"
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    division = db.Column(db.String(20), nullable=False, default="community", index=True)
    alt_text = db.Column(db.String(300), nullable=False)
    consent_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# Curriculum
# ---------------------------------------------------------------------------
class CurriculumModule(TimestampMixin, db.Model):
    """A course/level/practice description shown on the division pages.

    Empty fields are simply not displayed. `in_development` modules show their
    `launch_label` badge (e.g. "Launching 2027"). Research modules also drive the
    Research page's "Our 12-week Baguazhang program" section, which stays hidden
    until at least one research module is published.
    """
    __tablename__ = "curriculum_modules"
    id = db.Column(db.Integer, primary_key=True)
    division = db.Column(db.String(20), nullable=False, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    title = db.Column(db.String(200), nullable=False)
    age_range = db.Column(db.String(100))
    duration = db.Column(db.String(200))
    summary = db.Column(db.Text)
    format_notes = db.Column(db.JSON, nullable=False, default=list)    # e.g. "Free for families"
    learning_goals = db.Column(db.JSON, nullable=False, default=list)  # youth: what students learn; senior: what we practice
    projects = db.Column(db.JSON, nullable=False, default=list)        # youth: weekly projects; senior: progression
    adaptations = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="in_development", index=True)
    launch_label = db.Column(db.String(60))
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------
class ResearchReference(TimestampMixin, db.Model):
    __tablename__ = "research_references"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    authors = db.Column(db.String(500))
    year = db.Column(db.Integer)
    url = db.Column(db.String(500))
    summary = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, nullable=False, default=False, index=True)


class ResearchPartnerInquiry(TimestampMixin, db.Model):
    __tablename__ = "research_partner_inquiries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(150))
    email = db.Column(db.String(255), nullable=False)
    area_of_interest = db.Column(db.String(300))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)


class ResearchInterest(TimestampMixin, db.Model):
    """Community sign-up to hear about future research. Contact info only —
    deliberately NO health, medical, or diagnostic fields."""
    __tablename__ = "research_interest"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email_or_phone = db.Column(db.String(255), nullable=False)
    neighborhood = db.Column(db.String(100))
    consent_to_contact = db.Column(db.Boolean, nullable=False, default=False)


# ---------------------------------------------------------------------------
# Model-layer guards: run for every write path (API, Flask-Admin, CLI).
# ---------------------------------------------------------------------------
def _unique_slug(session, model, base, exclude_id=None):
    base = slugify(base)
    candidate, n = base, 2
    while True:
        q = select(model.id).where(model.slug == candidate)
        if exclude_id is not None:
            q = q.where(model.id != exclude_id)
        with session.no_autoflush:
            taken = session.scalar(q) is not None
        pending = any(
            o is not None and type(o) is model and o.slug == candidate and o.id != exclude_id
            for o in session.new
        )
        if not taken and not pending:
            return candidate
        candidate, n = f"{base}-{n}", n + 1


@event.listens_for(Session, "before_flush")
def _enforce_model_rules(session, flush_context, instances):
    for obj in list(session.new) + list(session.dirty):
        if getattr(type(obj), "__sluggable__", False):
            if not obj.slug:
                obj.slug = _unique_slug(session, type(obj), obj.title, obj.id)
            else:
                obj.slug = slugify(obj.slug)

        if isinstance(obj, Registration) and obj.type == "youth":
            # Never persist a youth participant's own email/phone.
            obj.email = None
            obj.phone = None

        if isinstance(obj, GalleryPhoto) and obj.is_published and not obj.consent_confirmed:
            raise ModelRuleError("A gallery photo cannot be published until consent_confirmed is true.")

        if isinstance(obj, NewsPost) and obj.is_published and obj.published_at is None:
            obj.published_at = utcnow()
