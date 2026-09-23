"""Public (no auth) API endpoints."""
from flask import Blueprint, Response, current_app, jsonify, request
from sqlalchemy import func, select

from ..extensions import db, limiter
from ..models import (REGISTRATION_TYPE_DIVISIONS, ContactMessage, Event, GalleryPhoto,
                      ImpactStat, NewsPost, Partner, Program, Registration, ResearchInterest,
                      ResearchPartnerInquiry, ResearchReference, SiteImage, SiteSetting,
                      TeamMember, Volunteer, utcnow)
from ..schemas import (ContactCreateSchema, EventSchema, GalleryPhotoSchema, ImpactStatSchema,
                       NewsPostSchema, PartnerSchema, ProgramSchema, RegistrationCreateSchema,
                       ResearchInquiryCreateSchema, ResearchInterestCreateSchema,
                       ResearchReferenceSchema, TeamMemberSchema, VolunteerCreateSchema)
from ..services import notifications
from ..services.ics import event_to_ics
from ..utils import (APIError, get_json, honeypot, load, local_now, paginate, parse_bool,
                     parse_list)

bp = Blueprint("public", __name__, url_prefix="/api")


def forms_limit():
    return current_app.config["RATELIMIT_FORMS"]


def _not_found(what="Item"):
    return APIError(f"{what} not found.", 404, "not_found")


def _division_filter(query, column, allowed):
    divisions = [d for d in parse_list(request.args.get("division")) if d in allowed]
    if request.args.get("division") and not divisions:
        raise APIError("Unknown division.", 400)
    return query.where(column.in_(divisions)) if divisions else query


def _neighborhood_filter(query, column):
    hood = (request.args.get("neighborhood") or "").strip()
    return query.where(func.lower(column) == hood.lower()) if hood else query


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------
program_public = ProgramSchema()


@bp.get("/programs")
def list_programs():
    q = select(Program)
    q = _division_filter(q, Program.division, ("youth", "senior", "intergenerational"))
    q = _neighborhood_filter(q, Program.neighborhood)
    active = (request.args.get("active") or "true").lower()
    if active != "all":
        q = q.where(Program.is_active.is_(parse_bool(active, True)))
    q = q.order_by(Program.start_date.is_(None), Program.start_date, Program.title)
    return jsonify({"items": program_public.dump(db.session.scalars(q).all(), many=True)})


@bp.get("/programs/<slug>")
def get_program(slug):
    program = db.session.scalar(select(Program).where(Program.slug == slug))
    if not program:
        raise _not_found("Program")
    return jsonify(program_public.dump(program))


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
event_public = EventSchema()


def _published_event(slug):
    ev = db.session.scalar(select(Event).where(Event.slug == slug, Event.is_published.is_(True)))
    if not ev:
        raise _not_found("Event")
    return ev


@bp.get("/events")
def list_events():
    q = select(Event).where(Event.is_published.is_(True))
    q = _division_filter(q, Event.division,
                         ("youth", "senior", "intergenerational", "research", "community"))
    q = _neighborhood_filter(q, Event.neighborhood)
    when = (request.args.get("when") or "upcoming").lower()
    ends = func.coalesce(Event.end_datetime, Event.start_datetime)
    now = local_now()
    if when == "upcoming":
        q = q.where(ends >= now).order_by(Event.start_datetime.asc())
    elif when == "past":
        q = q.where(ends < now).order_by(Event.start_datetime.desc())
    elif when == "all":
        q = q.order_by(Event.start_datetime.desc())
    else:
        raise APIError("`when` must be upcoming, past, or all.", 400)
    return jsonify(paginate(q, event_public, default_per_page=20))


@bp.get("/events/<slug>")
def get_event(slug):
    return jsonify(event_public.dump(_published_event(slug)))


@bp.get("/events/<slug>/ics")
def event_ics(slug):
    ev = _published_event(slug)
    body = event_to_ics(ev, current_app.config["SITE_URL"], current_app.config["ORG_NAME"])
    return Response(body, mimetype="text/calendar",
                    headers={"Content-Disposition": f'attachment; filename="{ev.slug}.ics"'})


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------
REG_OK = "Thank you! Your registration was received. We'll be in touch soon."
REG_WAITLIST = "This program is currently full, so you've been added to the waitlist. We'll contact you if a spot opens."


@bp.post("/registrations")
@limiter.limit(forms_limit)
@honeypot({"ok": True, "status": "pending", "waitlisted": False, "message": REG_OK})
def create_registration():
    data = load(RegistrationCreateSchema(), get_json())
    # Lock the program row (Postgres) so concurrent sign-ups can't oversell the last seat.
    program = db.session.scalar(
        select(Program).where(Program.id == data["program_id"]).with_for_update())
    if not program or not program.is_active:
        raise APIError("This program is not open for registration.", 400, "validation_error",
                       {"program_id": ["This program is not open for registration."]})
    if program.division not in REGISTRATION_TYPE_DIVISIONS[data["type"]]:
        raise APIError("This program doesn't accept that registration type.", 400,
                       "validation_error",
                       {"type": [f"{program.title} is a {program.division} program."]})

    status = "waitlist" if program.is_full else "pending"
    reg = Registration(**data, status=status)
    db.session.add(reg)
    db.session.commit()
    notifications.registration_received(reg)
    return jsonify({"ok": True, "status": status, "waitlisted": status == "waitlist",
                    "message": REG_WAITLIST if status == "waitlist" else REG_OK}), 201


VOL_OK = "Thank you for offering to volunteer! We'll reach out soon."


@bp.post("/volunteers")
@limiter.limit(forms_limit)
@honeypot({"ok": True, "message": VOL_OK})
def create_volunteer():
    vol = Volunteer(**load(VolunteerCreateSchema(), get_json()))
    db.session.add(vol)
    db.session.commit()
    notifications.volunteer_received(vol)
    return jsonify({"ok": True, "message": VOL_OK}), 201


CONTACT_OK = "Thanks for reaching out! We'll get back to you soon."


@bp.post("/contact")
@limiter.limit(forms_limit)
@honeypot({"ok": True, "message": CONTACT_OK})
def create_contact():
    msg = ContactMessage(**load(ContactCreateSchema(), get_json()))
    db.session.add(msg)
    db.session.commit()
    notifications.contact_received(msg)
    return jsonify({"ok": True, "message": CONTACT_OK}), 201


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------
news_list_schema = NewsPostSchema(exclude=("body",))
news_detail_schema = NewsPostSchema()


def _published_news():
    return select(NewsPost).where(NewsPost.is_published.is_(True),
                                  NewsPost.published_at <= utcnow())


@bp.get("/news")
def list_news():
    q = _published_news()
    category = request.args.get("category")
    if category:
        q = q.where(NewsPost.category == category)
    q = q.order_by(NewsPost.published_at.desc())
    return jsonify(paginate(q, news_list_schema, default_per_page=9, max_per_page=50))


@bp.get("/news/<slug>")
def get_news(slug):
    post = db.session.scalar(_published_news().where(NewsPost.slug == slug))
    if not post:
        raise _not_found("Post")
    return jsonify(news_detail_schema.dump(post))


# ---------------------------------------------------------------------------
# About / site content
# ---------------------------------------------------------------------------
@bp.get("/team")
def list_team():
    q = select(TeamMember)
    group = request.args.get("group")
    if group:
        q = q.where(TeamMember.group == group)
    q = q.order_by(TeamMember.sort_order, TeamMember.name)
    return jsonify({"items": TeamMemberSchema().dump(db.session.scalars(q).all(), many=True)})


@bp.get("/partners")
def list_partners():
    q = select(Partner)
    ptype = request.args.get("type")
    if ptype:
        q = q.where(Partner.type == ptype)
    q = q.order_by(Partner.sort_order, Partner.name)
    return jsonify({"items": PartnerSchema().dump(db.session.scalars(q).all(), many=True)})


@bp.get("/impact-stats")
def list_impact_stats():
    q = select(ImpactStat).order_by(ImpactStat.sort_order, ImpactStat.id)
    return jsonify({"items": ImpactStatSchema().dump(db.session.scalars(q).all(), many=True)})


@bp.get("/settings")
def public_settings():
    rows = db.session.scalars(select(SiteSetting).where(SiteSetting.is_public.is_(True)))
    return jsonify({s.key: s.value for s in rows})


@bp.get("/site-images")
def site_images():
    rows = db.session.scalars(select(SiteImage).order_by(SiteImage.slot_key))
    return jsonify({i.slot_key: {"image_url": i.image_url or None, "alt_text": i.alt_text or ""}
                    for i in rows})


@bp.get("/gallery")
def gallery():
    q = select(GalleryPhoto).where(GalleryPhoto.is_published.is_(True),
                                   GalleryPhoto.consent_confirmed.is_(True))
    q = _division_filter(q, GalleryPhoto.division,
                         ("youth", "senior", "intergenerational", "research", "community"))
    q = q.order_by(GalleryPhoto.sort_order, GalleryPhoto.created_at.desc())
    schema = GalleryPhotoSchema(only=("id", "image_url", "caption", "division", "alt_text",
                                      "created_at"))
    return jsonify(paginate(q, schema, default_per_page=24, max_per_page=100))


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------
@bp.get("/research/references")
def research_references():
    q = (select(ResearchReference).where(ResearchReference.is_verified.is_(True))
         .order_by(ResearchReference.year.desc(), ResearchReference.title))
    schema = ResearchReferenceSchema(exclude=("is_verified",))
    return jsonify({"items": schema.dump(db.session.scalars(q).all(), many=True)})


INQ_OK = "Thank you for your interest in research partnership. We'll follow up by email."


@bp.post("/research/inquiries")
@limiter.limit(forms_limit)
@honeypot({"ok": True, "message": INQ_OK})
def research_inquiry():
    inq = ResearchPartnerInquiry(**load(ResearchInquiryCreateSchema(), get_json()))
    db.session.add(inq)
    db.session.commit()
    notifications.research_inquiry_received(inq)
    return jsonify({"ok": True, "message": INQ_OK}), 201


INTEREST_OK = "Thank you! We'll contact you if future research opportunities become available."


@bp.post("/research/interest")
@limiter.limit(forms_limit)
@honeypot({"ok": True, "message": INTEREST_OK})
def research_interest():
    ri = ResearchInterest(**load(ResearchInterestCreateSchema(), get_json()))
    db.session.add(ri)
    db.session.commit()
    notifications.research_interest_received(ri)
    return jsonify({"ok": True, "message": INTEREST_OK}), 201
