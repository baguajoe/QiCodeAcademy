"""Admin API (JWT required): CRUD for every model, CSV exports, dashboard."""
from datetime import timedelta

from flask import Blueprint, g, jsonify, request
from sqlalchemy import Boolean, Integer, String, cast, func, or_, select

from ..extensions import db
from ..models import (REGISTRATION_STATUSES, WELLNESS_ACTIVITIES, WELLNESS_NEIGHBORHOODS, WELLNESS_PARTICIPATION,
                      WELLNESS_PARTNER_STATUSES, ContactMessage, CurriculumModule, Donation, Event, GalleryPhoto,
                      ImpactStat, NewsPost, Partner, Program, Registration, ResearchInterest,
                      ResearchPartnerInquiry, ResearchReference, SiteImage, SiteSetting,
                      TeamMember, User, Volunteer, WellnessDayInterest, WellnessDayPartner, utcnow)
from ..schemas import (ContactMessageSchema, CurriculumModuleSchema, DonationSchema, EventSchema, GalleryPhotoSchema,
                       ImpactStatSchema, NewsPostSchema, PartnerSchema, ProgramSchema,
                       RegistrationSchema, ResearchInterestSchema, ResearchPartnerInquirySchema,
                       ResearchReferenceSchema, SiteImageSchema, SiteSettingSchema,
                       TeamMemberSchema, UserSchema, VolunteerSchema, WellnessDayInterestSchema,
                       WellnessDayPartnerSchema)
from ..services import notifications
from ..utils import APIError, csv_response, get_json, load, paginate, parse_bool
from .auth import admin_required

bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")


_check_admin = admin_required(lambda: None)


@bp.before_request
def _require_admin():
    """Every /api/admin route requires an active admin's JWT (CORS preflight excepted)."""
    if request.method != "OPTIONS":
        return _check_admin()


# ---------------------------------------------------------------------------
# Generic CRUD
# ---------------------------------------------------------------------------
class Resource:
    def __init__(self, name, model, schema_cls, search=(), filters=(), default_sort="-created_at",
                 before_create=None, before_save=None, before_delete=None, after_update=None,
                 list_filters=None):
        self.name, self.model, self.schema_cls = name, model, schema_cls
        self.search, self.filters, self.default_sort = search, filters, default_sort
        # {query arg: (JSON list column, allowed values)} -> rows whose list contains that value
        self.list_filters = list_filters or {}
        self.before_create, self.before_save = before_create, before_save
        self.before_delete, self.after_update = before_delete, after_update

    @property
    def schema(self):
        return self.schema_cls()

    def get_or_404(self, obj_id):
        obj = db.session.get(self.model, obj_id)
        if obj is None:
            raise APIError(f"{self.name} #{obj_id} not found.", 404, "not_found")
        return obj

    def list(self):
        q = select(self.model)
        cols = self.model.__table__.columns
        for name in self.filters:
            raw = request.args.get(name)
            if raw is None or raw == "":
                continue
            col = cols[name]
            if isinstance(col.type, Boolean):
                q = q.where(col.is_(parse_bool(raw, False)))
            elif isinstance(col.type, Integer):
                try:
                    q = q.where(col == int(raw))
                except ValueError:
                    raise APIError(f"`{name}` must be an integer.", 400)
            else:
                q = q.where(col.in_([v for v in raw.split(",") if v]))
        for arg, (col_name, allowed) in self.list_filters.items():
            raw = request.args.get(arg)
            if raw:
                q = q.where(json_list_contains(self.model.__table__.columns[col_name], raw, allowed))
        term = (request.args.get("q") or "").strip()
        if term and self.search:
            like = f"%{term.lower()}%"
            q = q.where(or_(*[func.lower(cols[c]).like(like) for c in self.search]))
        q = q.order_by(*self._order())
        return jsonify(paginate(q, self.schema, default_per_page=50, max_per_page=500))

    def _order(self):
        sort = request.args.get("sort") or self.default_sort
        desc = sort.startswith("-")
        name = sort.lstrip("-")
        cols = self.model.__table__.columns
        if name not in cols:
            raise APIError(f"Cannot sort by `{name}`.", 400)
        col = cols[name]
        return [col.desc() if desc else col.asc(), cols["id"].desc() if desc else cols["id"].asc()]

    def create(self):
        payload = get_json()
        data = load(self.schema, payload)
        if self.before_create:
            self.before_create(data, payload)
        obj = self.model()
        self._apply(obj, data)
        db.session.add(obj)
        db.session.commit()
        return jsonify(self.schema.dump(obj)), 201

    def update(self, obj_id):
        obj = self.get_or_404(obj_id)
        payload = get_json()
        schema = self.schema
        # Merge onto current values and validate the *whole* record so cross-field
        # rules (youth contact rule, gallery consent, date ranges) always hold.
        current = {k: v for k, v in schema.dump(obj).items()
                   if k in schema.fields and not schema.fields[k].dump_only}
        data = load(schema, {**current, **payload})
        self._apply(obj, data)
        db.session.commit()
        if self.after_update:
            self.after_update(obj, current)
        return jsonify(self.schema.dump(obj))

    def delete(self, obj_id):
        obj = self.get_or_404(obj_id)
        if self.before_delete:
            self.before_delete(obj)
        db.session.delete(obj)
        db.session.commit()
        return jsonify({"ok": True, "deleted": obj_id})

    def _apply(self, obj, data):
        if self.before_save:
            data = self.before_save(obj, data) or data
        for k, v in data.items():
            setattr(obj, k, v)


def json_list_contains(col, value, allowed):
    """Portable "JSON list contains value" (SQLite + Postgres): match the quoted value in the
    serialized list. Values are checked against a fixed choice list, so no LIKE wildcards get in."""
    if value not in allowed:
        raise APIError(f"Unknown value `{value}`.", 400)
    return cast(col, String).like(f'%"{value}"%')


RESOURCES = {}


def register(resource):
    RESOURCES[resource.name] = resource
    base = f"/{resource.name}"
    ep = resource.name.replace("-", "_")
    bp.add_url_rule(base, f"{ep}_list", resource.list, methods=["GET"])
    bp.add_url_rule(base, f"{ep}_create", resource.create, methods=["POST"])
    bp.add_url_rule(f"{base}/<int:obj_id>", f"{ep}_get",
                    lambda obj_id, r=resource: jsonify(r.schema.dump(r.get_or_404(obj_id))),
                    methods=["GET"])
    bp.add_url_rule(f"{base}/<int:obj_id>", f"{ep}_update", resource.update,
                    methods=["PUT", "PATCH"])
    bp.add_url_rule(f"{base}/<int:obj_id>", f"{ep}_delete", resource.delete, methods=["DELETE"])


# --- Resource-specific hooks -------------------------------------------------
def _user_before_create(data, payload):
    if not data.get("password"):
        raise APIError("Password is required.", 400, "validation_error",
                       {"password": ["Password is required (min 10 characters)."]})


def _user_before_save(obj, data):
    data = dict(data)
    password = data.pop("password", None)
    if password:
        obj.set_password(password)
    if obj.id is not None and obj.id == g.current_user.id and data.get("is_active") is False:
        raise APIError("You can't deactivate your own account.", 400)
    return data


def _user_before_delete(obj):
    if obj.id == g.current_user.id:
        raise APIError("You can't delete your own account.", 400)


def _program_before_delete(obj):
    count = db.session.scalar(select(func.count(Registration.id))
                              .where(Registration.program_id == obj.id))
    if count:
        raise APIError(f"This program has {count} registration(s). Deactivate it instead "
                       "(set is_active to false), or delete its registrations first.", 409, "conflict")


def _registration_before_save(obj, data):
    if "program_id" in data and db.session.get(Program, data["program_id"]) is None:
        raise APIError("Program not found.", 400, "validation_error",
                       {"program_id": ["Program not found."]})
    return data


def _registration_after_update(obj, previous):
    # Email the family/participant when an admin confirms their spot.
    if obj.status == "confirmed" and previous.get("status") != "confirmed":
        notifications.registration_confirmed(obj)


for _r in [
    Resource("users", User, UserSchema, search=("email", "name"), filters=("is_active",),
             before_create=_user_before_create, before_save=_user_before_save,
             before_delete=_user_before_delete),
    Resource("programs", Program, ProgramSchema, search=("title", "neighborhood", "location"),
             filters=("division", "neighborhood", "is_active"), default_sort="-start_date",
             before_delete=_program_before_delete),
    Resource("events", Event, EventSchema, search=("title", "neighborhood", "location"),
             filters=("division", "neighborhood", "is_published"), default_sort="-start_datetime"),
    Resource("registrations", Registration, RegistrationSchema,
             search=("participant_first_name", "participant_last_name", "guardian_name",
                     "guardian_email", "email"),
             filters=("program_id", "type", "status", "photo_consent"), before_save=_registration_before_save,
             after_update=_registration_after_update),
    Resource("volunteers", Volunteer, VolunteerSchema, search=("name", "email")),
    Resource("contact-messages", ContactMessage, ContactMessageSchema,
             search=("name", "email", "subject", "organization"), filters=("type", "is_read")),
    Resource("donations", Donation, DonationSchema, search=("donor_name", "donor_email"),
             filters=("designation", "status", "recurring")),
    Resource("curriculum", CurriculumModule, CurriculumModuleSchema, search=("title", "summary"),
             filters=("division", "status", "is_published"), default_sort="sort_order"),
    Resource("news", NewsPost, NewsPostSchema, search=("title",),
             filters=("category", "is_published")),
    Resource("team", TeamMember, TeamMemberSchema, search=("name", "role_title"),
             filters=("group",), default_sort="sort_order"),
    Resource("partners", Partner, PartnerSchema, search=("name",), filters=("type",),
             default_sort="sort_order"),
    Resource("impact-stats", ImpactStat, ImpactStatSchema, default_sort="sort_order"),
    Resource("settings", SiteSetting, SiteSettingSchema, search=("key",), filters=("is_public",),
             default_sort="key"),
    Resource("site-images", SiteImage, SiteImageSchema, search=("slot_key",),
             default_sort="slot_key"),
    Resource("gallery", GalleryPhoto, GalleryPhotoSchema, search=("caption", "alt_text"),
             filters=("division", "is_published", "consent_confirmed")),
    Resource("research-references", ResearchReference, ResearchReferenceSchema,
             search=("title", "authors"), filters=("is_verified",)),
    Resource("research-inquiries", ResearchPartnerInquiry, ResearchPartnerInquirySchema,
             search=("name", "institution", "email"), filters=("is_read",)),
    Resource("research-interest", ResearchInterest, ResearchInterestSchema,
             search=("name", "email_or_phone", "neighborhood")),
    Resource("wellness-day-interest", WellnessDayInterest, WellnessDayInterestSchema,
             search=("name", "email", "phone"), filters=("neighborhood", "contact_method", "signing_up_for"),
             list_filters={"activity": ("activities", WELLNESS_ACTIVITIES)}),
    Resource("wellness-day-partners", WellnessDayPartner, WellnessDayPartnerSchema,
             search=("name", "organization", "email"), filters=("status", "show_publicly", "compensation"),
             list_filters={"participation_type": ("participation_types", WELLNESS_PARTICIPATION)}),
]:
    register(_r)


# ---------------------------------------------------------------------------
# CSV exports
# ---------------------------------------------------------------------------
@bp.get("/registrations/export.csv")
def export_registrations():
    q = select(Registration).join(Program).order_by(Program.title, Registration.created_at)
    if request.args.get("program_id"):
        q = q.where(Registration.program_id == request.args.get("program_id", type=int))
    if request.args.get("status"):
        q = q.where(Registration.status.in_(request.args["status"].split(",")))
    header = ["id", "created_at_utc", "status", "program", "division", "type",
              "participant_first_name", "participant_last_name", "grade",
              "guardian_name", "guardian_email", "guardian_phone",
              "email", "phone", "emergency_contact_name", "emergency_contact_phone",
              "photo_consent", "guardian_consent", "comfort_notes", "admin_notes"]
    rows = ([r.id, r.created_at.isoformat(timespec="seconds"), r.status, r.program.title,
             r.program.division, r.type, r.participant_first_name, r.participant_last_name,
             r.grade, r.guardian_name, r.guardian_email, r.guardian_phone, r.email, r.phone,
             r.emergency_contact_name, r.emergency_contact_phone, r.photo_consent,
             r.guardian_consent, r.comfort_notes, r.admin_notes]
            for r in db.session.scalars(q))
    return csv_response("registrations.csv", header, rows)


@bp.get("/volunteers/export.csv")
def export_volunteers():
    q = select(Volunteer).order_by(Volunteer.created_at.desc())
    header = ["id", "created_at_utc", "name", "email", "phone", "roles", "availability", "message"]
    rows = ([v.id, v.created_at.isoformat(timespec="seconds"), v.name, v.email, v.phone,
             v.roles or [], v.availability, v.message] for v in db.session.scalars(q))
    return csv_response("volunteers.csv", header, rows)


@bp.get("/research-interest/export.csv")
def export_research_interest():
    q = select(ResearchInterest).order_by(ResearchInterest.created_at.desc())
    header = ["id", "created_at_utc", "name", "email_or_phone", "neighborhood", "consent_to_contact"]
    rows = ([r.id, r.created_at.isoformat(timespec="seconds"), r.name, r.email_or_phone,
             r.neighborhood, r.consent_to_contact] for r in db.session.scalars(q))
    return csv_response("research-interest.csv", header, rows)


def _wellness_interest_query():
    q = select(WellnessDayInterest).order_by(WellnessDayInterest.created_at.desc())
    if request.args.get("neighborhood"):
        q = q.where(WellnessDayInterest.neighborhood.in_(request.args["neighborhood"].split(",")))
    if request.args.get("activity"):
        q = q.where(json_list_contains(WellnessDayInterest.activities, request.args["activity"], WELLNESS_ACTIVITIES))
    return q


@bp.get("/wellness-day-interest/export.csv")
def export_wellness_interest():
    header = ["id", "created_at_utc", "name", "email", "phone", "neighborhood", "activities",
              "contact_method", "signing_up_for", "consent_to_contact"]
    rows = ([r.id, r.created_at.isoformat(timespec="seconds"), r.name, r.email, r.phone, r.neighborhood,
             r.activities or [], r.contact_method, r.signing_up_for, r.consent_to_contact]
            for r in db.session.scalars(_wellness_interest_query()))
    return csv_response("wellness-day-interest.csv", header, rows)


@bp.get("/wellness-day-partners/export.csv")
def export_wellness_partners():
    q = select(WellnessDayPartner).order_by(WellnessDayPartner.created_at.desc())
    if request.args.get("status"):
        q = q.where(WellnessDayPartner.status.in_(request.args["status"].split(",")))
    if request.args.get("participation_type"):
        q = q.where(json_list_contains(WellnessDayPartner.participation_types,
                                       request.args["participation_type"], WELLNESS_PARTICIPATION))
    header = ["id", "created_at_utc", "status", "show_publicly", "name", "organization", "email", "phone",
              "website_or_social", "participation_types", "offer_description", "license_type", "license_number",
              "has_insurance", "compensation", "typical_rate", "setup_needs", "availability", "referral_source",
              "agrees_no_sales", "agrees_not_confirmed", "admin_notes"]
    rows = ([p.id, p.created_at.isoformat(timespec="seconds"), p.status, p.show_publicly, p.name, p.organization,
             p.email, p.phone, p.website_or_social, p.participation_types or [], p.offer_description, p.license_type,
             p.license_number, p.has_insurance, p.compensation, p.typical_rate, p.setup_needs or [],
             p.availability or [], p.referral_source, p.agrees_no_sales, p.agrees_not_confirmed, p.admin_notes]
            for p in db.session.scalars(q))
    return csv_response("wellness-day-partners.csv", header, rows)


@bp.get("/wellness-day/summary")
def wellness_day_summary():
    """Interest-list totals and breakdowns, partner counts, and the confirmed lineup."""
    interest = db.session.scalars(select(WellnessDayInterest)).all()
    by_activity = {a: 0 for a in WELLNESS_ACTIVITIES}
    by_hood = {h: 0 for h in WELLNESS_NEIGHBORHOODS}
    not_given = 0
    for r in interest:
        for a in r.activities or []:
            if a in by_activity:
                by_activity[a] += 1
        if r.neighborhood in by_hood:
            by_hood[r.neighborhood] += 1
        else:
            not_given += 1
    partners = db.session.scalars(select(WellnessDayPartner)).all()
    by_type = {t: 0 for t in WELLNESS_PARTICIPATION}
    for p in partners:
        for t in p.participation_types or []:
            if t in by_type:
                by_type[t] += 1
    confirmed = sorted((p for p in partners if p.status == "confirmed"), key=lambda p: p.display_name.lower())
    return jsonify({
        "interest_total": len(interest),
        "interest_by_activity": by_activity,
        "interest_by_neighborhood": {**by_hood, "not_given": not_given},
        "partners_total": len(partners),
        "partners_by_status": {s: sum(p.status == s for p in partners) for s in WELLNESS_PARTNER_STATUSES},
        "partners_by_type": by_type,
        "confirmed_lineup": WellnessDayPartnerSchema(
            only=("id", "name", "organization", "display_name", "email", "phone", "participation_types",
                  "show_publicly", "license_type", "license_number", "has_insurance", "setup_needs",
                  "availability")).dump(confirmed, many=True),
    })


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@bp.get("/dashboard")
def dashboard():
    # Registrations by program and status (one grouped query).
    counts = {}
    for pid, status, n in db.session.execute(
            select(Registration.program_id, Registration.status, func.count(Registration.id))
            .group_by(Registration.program_id, Registration.status)):
        counts.setdefault(pid, {})[status] = n
    programs = db.session.scalars(select(Program).order_by(Program.is_active.desc(), Program.title))
    by_program = []
    for p in programs:
        c = {s: counts.get(p.id, {}).get(s, 0) for s in REGISTRATION_STATUSES}
        held = c["pending"] + c["confirmed"]
        by_program.append({
            "program_id": p.id, "title": p.title, "slug": p.slug, "division": p.division,
            "is_active": p.is_active, "capacity": p.capacity,
            "seats_left": None if p.capacity is None else max(p.capacity - held, 0),
            "total": sum(c.values()), **c,
        })

    totals = {d: {"amount_cents": 0, "count": 0} for d in ("youth", "senior", "research", "general")}
    for designation, amount, n in db.session.execute(
            select(Donation.designation, func.sum(Donation.amount_cents), func.count(Donation.id))
            .where(Donation.status == "completed").group_by(Donation.designation)):
        totals[designation] = {"amount_cents": int(amount or 0), "count": n}
    recent = db.session.scalars(select(Donation).where(Donation.status == "completed")
                                .order_by(Donation.created_at.desc()).limit(10)).all()
    active_monthly = db.session.scalar(
        select(func.count(Donation.id)).where(Donation.recurring.is_(True),
                                              Donation.stripe_session_id.is_not(None),
                                              Donation.subscription_status == "active"))
    since = utcnow() - timedelta(days=30)

    def count(model, *where):
        return db.session.scalar(select(func.count(model.id)).where(*where)) or 0

    return jsonify({
        "registrations_by_program": by_program,
        "registrations_pending": count(Registration, Registration.status == "pending"),
        "registrations_waitlist": count(Registration, Registration.status == "waitlist"),
        "donations": {
            "recent": DonationSchema().dump(recent, many=True),
            "totals_by_designation": totals,
            "total_amount_cents": sum(t["amount_cents"] for t in totals.values()),
            "last_30_days_amount_cents": int(db.session.scalar(
                select(func.coalesce(func.sum(Donation.amount_cents), 0))
                .where(Donation.status == "completed", Donation.created_at >= since)) or 0),
            "active_monthly_donors": active_monthly or 0,
        },
        "unread_messages": count(ContactMessage, ContactMessage.is_read.is_(False)),
        "unread_messages_by_type": {
            t: count(ContactMessage, ContactMessage.is_read.is_(False), ContactMessage.type == t)
            for t in ("general", "guest_instructor", "partner")},
        "new_research_inquiries": count(ResearchPartnerInquiry,
                                        ResearchPartnerInquiry.is_read.is_(False)),
        "research_interest_total": count(ResearchInterest),
        "volunteers_last_30_days": count(Volunteer, Volunteer.created_at >= since),
        "wellness_interest_total": count(WellnessDayInterest),
        "wellness_partners_new": count(WellnessDayPartner, WellnessDayPartner.status == "new"),
    })
