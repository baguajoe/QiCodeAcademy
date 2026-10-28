"""Flask-Admin backup back-office at /flask-admin.

The React admin (built later) is the primary UI; this is a fallback that works
with no frontend. It uses a session login (same admin users as the API), CSRF-
protected forms, and the same model-layer guards (slugs, sanitizing, youth
contact rule, gallery consent) via the SQLAlchemy before_flush hook.
"""
import hmac
import secrets
from datetime import timedelta

from flask import current_app, flash, redirect, request, session, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter, FilterEqual
from flask_admin.form import SecureForm
from flask_admin.menu import MenuLink
from flask_admin.theme import Bootstrap4Theme
from sqlalchemy import String, cast, func, select
from wtforms import PasswordField, SelectField, SelectMultipleField
from wtforms.validators import Length, Optional

from . import models as m
from .extensions import db, limiter

SESSION_KEY = "flask_admin_user_id"


def current_admin():
    uid = session.get(SESSION_KEY)
    if not uid:
        return None
    user = db.session.get(m.User, uid)
    if user is None or not user.is_active:
        session.pop(SESSION_KEY, None)
        return None
    return user


def _choices(values):
    return [(v, v.replace("_", " ").title()) for v in values]


class SecureModelView(ModelView):
    form_base_class = SecureForm  # CSRF on every create/edit/delete form
    page_size = 50
    can_view_details = True
    form_excluded_columns = ("created_at", "updated_at", "slug")
    column_exclude_list = ("updated_at",)
    column_default_sort = ("created_at", True)

    def is_accessible(self):
        return current_admin() is not None

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.login_view", next=request.full_path))


def choice_overrides(**fields):
    return {name: SelectField for name in fields}, {
        name: {"choices": _choices(values)} for name, values in fields.items()}


def make_view(model, name, category=None, choices=None, **attrs):
    """Build a ModelView subclass with select fields for enum-like string columns."""
    overrides, args = choice_overrides(**(choices or {}))
    attrs.setdefault("form_overrides", {}).update(overrides)
    attrs.setdefault("form_args", {}).update(args)
    view_cls = type(f"{model.__name__}AdminView", (SecureModelView,), attrs)
    return view_cls(model, db.session, name=name, category=category,
                    endpoint=f"fa_{model.__tablename__}")


class UserAdminView(SecureModelView):
    column_list = ("email", "name", "is_active", "last_login_at", "created_at")
    column_searchable_list = ("email", "name")
    form_excluded_columns = ("password_hash", "created_at", "updated_at", "last_login_at")
    column_exclude_list = ("password_hash",)
    column_details_exclude_list = ("password_hash",)
    can_export = False
    form_extra_fields = {
        "new_password": PasswordField("New password", validators=[Optional(), Length(min=10, max=200)],
                                      description="Required when creating a user. Leave blank to keep the current password."),
    }

    def on_model_change(self, form, model, is_created):
        if form.new_password.data:
            model.set_password(form.new_password.data)
        elif is_created:
            raise ValueError("A password (min 10 characters) is required for new users.")
        if model.id == getattr(current_admin(), "id", None) and not model.is_active:
            raise ValueError("You can't deactivate your own account.")

    def on_model_delete(self, model):
        if model.id == getattr(current_admin(), "id", None):
            raise ValueError("You can't delete your own account.")


class VolunteerAdminView(SecureModelView):
    column_list = ("name", "email", "phone", "roles", "created_at")
    column_searchable_list = ("name", "email")
    form_overrides = {"roles": SelectMultipleField}
    form_args = {"roles": {"choices": _choices(m.VOLUNTEER_ROLES)}}


class ProgramAdminView(SecureModelView):
    column_list = ("title", "division", "neighborhood", "start_date", "capacity", "is_active")
    column_searchable_list = ("title", "neighborhood")
    column_filters = ("division", "neighborhood", "is_active")
    column_default_sort = ("start_date", True)
    form_excluded_columns = ("created_at", "updated_at", "slug", "registrations")
    form_overrides = {"division": SelectField}
    form_args = {"division": {"choices": _choices(m.PROGRAM_DIVISIONS)}}

    def on_model_delete(self, model):
        if db.session.scalar(select(func.count(m.Registration.id))
                             .where(m.Registration.program_id == model.id)):
            raise ValueError("This program has registrations — deactivate it instead.")


# --- Senior Wellness Day ----------------------------------------------------
from .services.notifications import WELLNESS_ACTIVITY_LABELS, WELLNESS_PARTICIPATION_LABELS  # noqa: E402

PARTNER_STATUS_CHOICES = [(s, s.title()) for s in m.WELLNESS_PARTNER_STATUSES]


class JsonListContainsFilter(BaseSQLAFilter):
    """Rows whose JSON list column contains the chosen value (portable: matches the quoted value)."""

    def apply(self, query, value, alias=None):
        allowed = {v for v, _ in self.options}
        if value not in allowed:
            return query
        return query.filter(cast(self.get_column(alias), String).like(f'%"{value}"%'))

    def operation(self):
        return "includes"


def _labels(values, mapping):
    return ", ".join(mapping.get(v, v) for v in values or [])


class WellnessInterestAdminView(SecureModelView):
    list_template = "flask_admin_custom/wellness_interest_list.html"
    can_export = True
    column_list = ("name", "email", "phone", "neighborhood", "activities", "contact_method", "signing_up_for",
                   "created_at")
    column_searchable_list = ("name", "email", "phone")
    column_filters = (
        FilterEqual(m.WellnessDayInterest.neighborhood, "Neighborhood",
                    options=[(h, h) for h in m.WELLNESS_NEIGHBORHOODS]),
        JsonListContainsFilter(m.WellnessDayInterest.activities, "Activity",
                               options=list(WELLNESS_ACTIVITY_LABELS.items())),
    )
    column_formatters = {"activities": lambda v, c, mdl, n: _labels(mdl.activities, WELLNESS_ACTIVITY_LABELS)}
    form_overrides = {"activities": SelectMultipleField, "neighborhood": SelectField,
                      "contact_method": SelectField, "signing_up_for": SelectField}
    form_args = {"activities": {"choices": list(WELLNESS_ACTIVITY_LABELS.items())},
                 "neighborhood": {"choices": [("", "—")] + [(h, h) for h in m.WELLNESS_NEIGHBORHOODS]},
                 "contact_method": {"choices": [("", "—")] + _choices(m.WELLNESS_CONTACT_METHODS)},
                 "signing_up_for": {"choices": [("", "—")] + _choices(m.WELLNESS_SIGNUP_FOR)}}
    column_descriptions = {"name": "No age, birth date, or health information is collected — by design."}

    @expose("/")
    def index_view(self):
        rows = db.session.scalars(select(m.WellnessDayInterest)).all()
        acts = {k: 0 for k in WELLNESS_ACTIVITY_LABELS}
        hoods = {h: 0 for h in m.WELLNESS_NEIGHBORHOODS}
        for r in rows:
            for a in r.activities or []:
                if a in acts:
                    acts[a] += 1
            if r.neighborhood in hoods:
                hoods[r.neighborhood] += 1
        self._template_args["wellness_summary"] = {
            "total": len(rows),
            "by_activity": [(WELLNESS_ACTIVITY_LABELS[k], n) for k, n in acts.items()],
            "by_neighborhood": list(hoods.items()) + [("Not given", len(rows) - sum(hoods.values()))],
        }
        return super().index_view()

    def on_model_change(self, form, model, is_created):
        model.neighborhood = model.neighborhood or None
        model.contact_method = model.contact_method or None
        model.signing_up_for = model.signing_up_for or None
        if not model.email and not model.phone:
            raise ValueError("Enter an email address or a phone number.")


class WellnessPartnerAdminView(SecureModelView):
    can_export = True
    column_list = ("name", "organization", "participation_types", "status", "show_publicly", "email", "created_at")
    column_searchable_list = ("name", "organization", "email")
    column_filters = (
        FilterEqual(m.WellnessDayPartner.status, "Status", options=PARTNER_STATUS_CHOICES),
        JsonListContainsFilter(m.WellnessDayPartner.participation_types, "Participation type",
                               options=list(WELLNESS_PARTICIPATION_LABELS.items())),
        "show_publicly",
    )
    column_formatters = {"participation_types": lambda v, c, mdl, n: _labels(mdl.participation_types,
                                                                             WELLNESS_PARTICIPATION_LABELS)}
    column_formatters_export = {}
    form_overrides = {"participation_types": SelectMultipleField, "setup_needs": SelectMultipleField,
                      "availability": SelectMultipleField, "status": SelectField, "has_insurance": SelectField,
                      "compensation": SelectField}
    form_args = {"participation_types": {"choices": list(WELLNESS_PARTICIPATION_LABELS.items())},
                 "setup_needs": {"choices": _choices(m.WELLNESS_SETUP_NEEDS)},
                 "availability": {"choices": _choices(m.WELLNESS_AVAILABILITY)},
                 "status": {"choices": PARTNER_STATUS_CHOICES},
                 "has_insurance": {"choices": [("", "—")] + _choices(m.WELLNESS_INSURANCE)},
                 "compensation": {"choices": [("", "—")] + _choices(m.WELLNESS_COMPENSATION)}}
    column_descriptions = {
        "show_publicly": "Listed in \"Who's joining us\" on the public page ONLY when status is Confirmed too "
                         "(organization or name + participation type only).",
        "license_number": "Required for practitioners (Massachusetts license for massage/bodywork)."}

    def on_model_change(self, form, model, is_created):
        model.has_insurance = model.has_insurance or None
        model.compensation = model.compensation or None
        if "practitioner" in (model.participation_types or []) and not (model.license_type and model.license_number):
            raise ValueError("Practitioners need a license type and number.")


class WellnessLineupAdminView(WellnessPartnerAdminView):
    """Confirmed partners only (the working lineup; "show publicly" controls the public list)."""
    can_create = False
    column_list = ("display_name", "participation_types", "show_publicly", "email", "phone", "license_number",
                   "has_insurance", "setup_needs")
    column_labels = {"display_name": "Organization / name"}
    column_default_sort = None

    def get_query(self):
        return super().get_query().filter(m.WellnessDayPartner.status == "confirmed")

    def get_count_query(self):
        return super().get_count_query().filter(m.WellnessDayPartner.status == "confirmed")


class SecureIndexView(AdminIndexView):
    def is_visible(self):
        return True

    @expose("/")
    def index(self):
        if not current_admin():
            return redirect(url_for(".login_view"))
        counts = {
            "Pending registrations": db.session.scalar(
                select(func.count(m.Registration.id)).where(m.Registration.status == "pending")),
            "Unread messages": db.session.scalar(
                select(func.count(m.ContactMessage.id)).where(m.ContactMessage.is_read.is_(False))),
            "New research inquiries": db.session.scalar(
                select(func.count(m.ResearchPartnerInquiry.id)).where(m.ResearchPartnerInquiry.is_read.is_(False))),
            "Senior Wellness Day interest sign-ups": db.session.scalar(select(func.count(m.WellnessDayInterest.id))),
            "New Senior Wellness Day partner submissions": db.session.scalar(
                select(func.count(m.WellnessDayPartner.id)).where(m.WellnessDayPartner.status == "new")),
        }
        return self.render("flask_admin_custom/index.html", user=current_admin(), counts=counts)

    @expose("/login", methods=["GET", "POST"])
    @limiter.limit(lambda: current_app.config["RATELIMIT_LOGIN"], methods=["POST"])
    def login_view(self):
        if request.method == "POST":
            token = session.get("fa_login_csrf", "")
            if not token or not hmac.compare_digest(token, request.form.get("csrf_token", "")):
                flash("Your session expired. Please try again.", "error")
                return redirect(url_for(".login_view"))
            email = (request.form.get("email") or "").strip().lower()
            user = db.session.scalar(select(m.User).where(m.User.email == email))
            if user and user.is_active and user.check_password(request.form.get("password") or ""):
                session.clear()  # prevent session fixation
                session.permanent = True
                session[SESSION_KEY] = user.id
                user.last_login_at = m.utcnow()
                db.session.commit()
                nxt = request.args.get("next") or ""
                # Only allow local redirects back into the panel.
                if not nxt.startswith("/flask-admin") or nxt.startswith("//"):
                    nxt = url_for(".index")
                return redirect(nxt)
            flash("Invalid email or password.", "error")
        session["fa_login_csrf"] = secrets.token_urlsafe(32)
        return self.render("flask_admin_custom/login.html", csrf_token=session["fa_login_csrf"])

    @expose("/logout", methods=["GET", "POST"])
    def logout_view(self):
        session.clear()
        return redirect(url_for(".login_view"))


class AuthMenuLink(MenuLink):
    def is_accessible(self):
        return current_admin() is not None


def init_admin_panel(app):
    app.config.setdefault("PERMANENT_SESSION_LIFETIME", timedelta(hours=8))
    admin = Admin(app, name="Qi Code Academy", url="/flask-admin",
                  index_view=SecureIndexView(url="/flask-admin", name="Home"),
                  theme=Bootstrap4Theme(swatch="flatly"))

    people = "People & Forms"
    admin.add_view(make_view(
        m.Registration, "Registrations", people,
        choices={"type": m.REGISTRATION_TYPES, "status": m.REGISTRATION_STATUSES},
        column_list=("participant_first_name", "participant_last_name", "type", "program",
                     "status", "guardian_email", "email", "created_at"),
        column_filters=("type", "status", "program.title"),
        column_searchable_list=("participant_first_name", "participant_last_name",
                                "guardian_name", "guardian_email", "email"),
        column_descriptions={"email": "Seniors only — never stored for youth.",
                             "phone": "Seniors only — never stored for youth."}))
    admin.add_view(VolunteerAdminView(m.Volunteer, db.session, name="Volunteers", category=people,
                                      endpoint="fa_volunteers"))
    admin.add_view(make_view(
        m.ContactMessage, "Messages", people, choices={"type": m.CONTACT_TYPES},
        column_list=("name", "email", "type", "subject", "is_read", "created_at"),
        column_filters=("type", "is_read"), column_searchable_list=("name", "email", "subject")))
    admin.add_view(make_view(
        m.Donation, "Donations", people,
        choices={"designation": m.DONATION_DESIGNATIONS, "status": m.DONATION_STATUSES},
        column_list=("created_at", "amount_cents", "recurring", "designation", "donor_name",
                     "donor_email", "status", "subscription_status"),
        column_filters=("designation", "status", "recurring"),
        column_formatters={"amount_cents": lambda v, c, mdl, n: f"${mdl.amount_cents / 100:,.2f}"}))

    programs = "Programs & Events"
    admin.add_view(ProgramAdminView(m.Program, db.session, name="Programs", category=programs,
                                    endpoint="fa_programs"))
    admin.add_view(make_view(
        m.Event, "Events", programs, choices={"division": m.EVENT_DIVISIONS},
        column_list=("title", "division", "start_datetime", "neighborhood", "is_published"),
        column_filters=("division", "is_published"), column_searchable_list=("title",),
        column_default_sort=("start_datetime", True),
        column_descriptions={"start_datetime": "Boston local time",
                             "end_datetime": "Boston local time"}))

    content = "Content"
    admin.add_view(make_view(
        m.NewsPost, "News", content, choices={"category": m.NEWS_CATEGORIES},
        column_list=("title", "category", "is_published", "published_at"),
        column_filters=("category", "is_published"), column_searchable_list=("title",),
        column_descriptions={"body": "HTML; sanitized automatically on save."}))
    admin.add_view(make_view(
        m.GalleryPhoto, "Gallery", content, choices={"division": m.GALLERY_DIVISIONS},
        column_list=("image_url", "alt_text", "division", "consent_confirmed", "is_published"),
        column_filters=("division", "is_published", "consent_confirmed"),
        column_descriptions={"is_published": "Requires consent_confirmed."}))
    admin.add_view(make_view(m.TeamMember, "Team", content, choices={"group": m.TEAM_GROUPS},
                             column_list=("name", "role_title", "group", "sort_order"),
                             column_default_sort="sort_order"))
    admin.add_view(make_view(m.Partner, "Partners", content, choices={"type": m.PARTNER_TYPES},
                             column_list=("name", "type", "website_url", "sort_order"),
                             column_default_sort="sort_order"))
    admin.add_view(make_view(m.ImpactStat, "Impact stats", content,
                             column_list=("label", "value", "sort_order"),
                             column_default_sort="sort_order"))
    admin.add_view(make_view(m.SiteImage, "Site images", content,
                             column_list=("slot_key", "image_url", "alt_text"),
                             column_default_sort="slot_key"))
    admin.add_view(make_view(m.SiteSetting, "Settings", content,
                             column_list=("key", "value", "is_public"),
                             column_default_sort="key"))

    admin.add_view(make_view(
        m.CurriculumModule, "Curriculum", programs,
        choices={"division": m.CURRICULUM_DIVISIONS, "status": m.CURRICULUM_STATUSES},
        column_list=("title", "division", "status", "launch_label", "sort_order", "is_published"),
        column_filters=("division", "status", "is_published"), column_searchable_list=("title",),
        column_default_sort="sort_order",
        column_descriptions={
            "learning_goals": 'JSON list, e.g. ["First item", "Second item"]. Youth: what students learn. Seniors: what we practice.',
            "projects": "JSON list. Youth: weekly projects. Seniors: progression steps.",
            "format_notes": 'JSON list of short facts, e.g. ["Free for families"].'}))

    research = "Research"
    admin.add_view(make_view(m.ResearchReference, "References", research,
                             column_list=("title", "authors", "year", "is_verified"),
                             column_filters=("is_verified",)))
    admin.add_view(make_view(m.ResearchPartnerInquiry, "Partner inquiries", research,
                             column_list=("name", "institution", "email", "is_read", "created_at"),
                             column_filters=("is_read",)))
    admin.add_view(make_view(m.ResearchInterest, "Interest sign-ups", research,
                             column_list=("name", "email_or_phone", "neighborhood",
                                          "consent_to_contact", "created_at")))

    wellness = "Senior Wellness Day"
    admin.add_view(WellnessInterestAdminView(m.WellnessDayInterest, db.session, name="Interest list",
                                             category=wellness, endpoint="fa_wellness_day_interest"))
    admin.add_view(WellnessPartnerAdminView(m.WellnessDayPartner, db.session, name="Partners, vendors & volunteers",
                                            category=wellness, endpoint="fa_wellness_day_partners"))
    admin.add_view(WellnessLineupAdminView(m.WellnessDayPartner, db.session, name="Confirmed lineup",
                                           category=wellness, endpoint="fa_wellness_day_lineup"))

    admin.add_view(UserAdminView(m.User, db.session, name="Admin users", category="Settings",
                                 endpoint="fa_users"))
    admin.add_link(AuthMenuLink(name="Log out", url="/flask-admin/logout"))
    return admin
