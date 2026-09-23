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
from flask_admin.form import SecureForm
from flask_admin.menu import MenuLink
from flask_admin.theme import Bootstrap4Theme
from sqlalchemy import func, select
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

    admin.add_view(UserAdminView(m.User, db.session, name="Admin users", category="Settings",
                                 endpoint="fa_users"))
    admin.add_link(AuthMenuLink(name="Log out", url="/flask-admin/logout"))
    return admin
