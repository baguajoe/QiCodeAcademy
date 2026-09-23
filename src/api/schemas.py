"""Marshmallow schemas: server-side validation for every write, and JSON output.

- Public form schemas (`*CreateSchema`) drop blank strings and ignore unknown keys
  (including the honeypot field `website`).
- Admin model schemas are used for admin CRUD load/dump and, with `only`/
  `exclude`, for public output. Password hashes are never part of any schema.
"""
import html
import re

from marshmallow import (EXCLUDE, Schema, ValidationError, fields, post_load, pre_load,
                         validate, validates_schema)

from . import models as m
from .sanitize import strip_tags
from .utils import iso_utc, to_local_naive

PHONE_RE = re.compile(r"^[0-9+().\-\s]*(?:(?:ext|x)\.?\s*\d{1,6})?$", re.IGNORECASE)


def _phone(value):
    if value is None:
        return
    digits = re.sub(r"\D", "", value)
    if not PHONE_RE.match(value) or not (7 <= len(digits) <= 20):
        raise ValidationError("Enter a valid phone number.")


def _is_email(value):
    try:
        fields.Email()._validate(value)
        return True
    except ValidationError:
        return False


def S(max_len, required=False, **kw):
    """String field with a max length. Optional strings accept null."""
    kw.setdefault("validate", validate.Length(max=max_len))
    return fields.String(required=required, allow_none=not required, **kw)


def Req(max_len, **kw):
    return fields.String(required=True, validate=validate.Length(min=1, max=max_len), **kw)


def Choice(choices, required=False, **kw):
    return fields.String(required=required, validate=validate.OneOf(choices), **kw)


URL_RE = validate.Regexp(r"^(https?://[^\s]+|/[^\s]*)?$", error="Enter a full http(s) URL or a /path.")


def Url(required=False, **kw):
    # Accept absolute http(s) URLs or site-relative paths like /uploads/x.webp.
    return fields.String(required=required, allow_none=not required,
                         validate=validate.And(validate.Length(min=int(required), max=500), URL_RE), **kw)


Phone = lambda required=False: fields.String(  # noqa: E731
    required=required, allow_none=not required, validate=_phone)
Email = lambda required=False: fields.Email(  # noqa: E731
    required=required, allow_none=not required, validate=validate.Length(max=255))


class UTCDateTime(fields.DateTime):
    """Stored naive-UTC; serialized with a trailing Z."""

    def _serialize(self, value, attr, obj, **kwargs):
        return iso_utc(value)

    def _deserialize(self, value, attr, data, **kwargs):
        dt = super()._deserialize(value, attr, data, **kwargs)
        if dt.tzinfo is not None:
            from datetime import timezone
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt


class LocalDateTime(fields.DateTime):
    """Boston wall-clock time (events). Offsets on input are converted to Boston time."""

    def _serialize(self, value, attr, obj, **kwargs):
        return value.isoformat(timespec="minutes") if value else None

    def _deserialize(self, value, attr, data, **kwargs):
        return to_local_naive(super()._deserialize(value, attr, data, **kwargs))


# ---------------------------------------------------------------------------
# Bases
# ---------------------------------------------------------------------------
class PublicFormSchema(Schema):
    """Public inputs: trim strings, treat blanks as missing, ignore unknown keys."""

    class Meta:
        unknown = EXCLUDE

    @pre_load
    def _clean(self, data, **kwargs):
        if not isinstance(data, dict):
            raise ValidationError("Expected a JSON object.")
        out = {}
        for k, v in data.items():
            if isinstance(v, str):
                v = v.strip()
                if v == "":
                    continue
            out[k] = v
        return out


class AdminSchema(Schema):
    """Admin model schema: trims strings, blank -> null, ignores unknown/readonly keys."""

    id = fields.Integer(dump_only=True)
    created_at = UTCDateTime(dump_only=True)
    updated_at = UTCDateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def _clean(self, data, **kwargs):
        if not isinstance(data, dict):
            raise ValidationError("Expected a JSON object.")
        return {k: (v.strip() or None) if isinstance(v, str) else v for k, v in data.items()}


# ---------------------------------------------------------------------------
# Programs / events
# ---------------------------------------------------------------------------
class ProgramSchema(AdminSchema):
    division = Choice(m.PROGRAM_DIVISIONS, required=True)
    title = Req(200)
    slug = S(200, validate=validate.Regexp(r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
                                          error="Use lowercase letters, numbers and dashes."))
    description = S(20000)
    age_range = S(100)
    neighborhood = S(100)
    location = S(255)
    schedule = S(255)
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    capacity = fields.Integer(allow_none=True, validate=validate.Range(min=0, max=100000))
    cost = S(100)
    is_active = fields.Boolean(load_default=True)
    image_url = Url()
    seats_left = fields.Integer(dump_only=True)
    is_full = fields.Boolean(dump_only=True)

    @validates_schema
    def _dates(self, data, **kwargs):
        if data.get("start_date") and data.get("end_date") and data["end_date"] < data["start_date"]:
            raise ValidationError({"end_date": ["End date must be on or after the start date."]})

    @post_load
    def _defaults(self, data, **kwargs):
        if "description" in data and data["description"] is None:
            data["description"] = ""
        return data


class EventSchema(AdminSchema):
    division = Choice(m.EVENT_DIVISIONS, required=True)
    title = Req(200)
    slug = ProgramSchema._declared_fields["slug"]
    description = S(20000)
    neighborhood = S(100)
    location = S(255)
    start_datetime = LocalDateTime(required=True)
    end_datetime = LocalDateTime(allow_none=True)
    image_url = Url()
    is_published = fields.Boolean(load_default=False)
    timezone = fields.Function(lambda obj: "America/New_York", dump_only=True)

    @validates_schema
    def _times(self, data, **kwargs):
        s, e = data.get("start_datetime"), data.get("end_datetime")
        if s and e and e < s:
            raise ValidationError({"end_datetime": ["End must be after the start."]})

    @post_load
    def _defaults(self, data, **kwargs):
        if "description" in data and data["description"] is None:
            data["description"] = ""
        return data


# ---------------------------------------------------------------------------
# Registrations
# ---------------------------------------------------------------------------
YOUTH_ONLY = ("guardian_name", "guardian_email", "guardian_phone", "grade", "guardian_consent")
SENIOR_ONLY = ("email", "phone", "comfort_notes")


class _RegistrationFields:
    program_id = fields.Integer(required=True)
    type = Choice(m.REGISTRATION_TYPES, required=True)
    guardian_name = S(120)
    guardian_email = Email()
    guardian_phone = Phone()
    participant_first_name = Req(80)
    participant_last_name = Req(80)
    grade = S(20)
    email = Email()
    phone = Phone()
    emergency_contact_name = Req(120)
    emergency_contact_phone = Phone(required=True)
    photo_consent = fields.Boolean(required=True)
    guardian_consent = fields.Boolean(allow_none=True)
    comfort_notes = S(2000)


def validate_registration(data):
    """Youth vs senior rules. Raises ValidationError; returns cleaned data."""
    errors = {}
    rtype = data.get("type")
    if rtype == "youth":
        for f in ("guardian_name", "guardian_email", "guardian_phone", "grade"):
            if not data.get(f):
                errors[f] = ["Required for youth registrations."]
        if data.get("guardian_consent") is not True:
            errors["guardian_consent"] = ["A parent or guardian must give consent."]
        for f in ("email", "phone"):
            if data.get(f):
                errors[f] = ["We don't collect a youth participant's email or phone — "
                             "please use the guardian's contact details."]
        if errors:
            raise ValidationError(errors)
        data["email"] = data["phone"] = data["comfort_notes"] = None
    elif rtype == "senior":
        if not data.get("email") and not data.get("phone"):
            errors["email"] = ["Provide an email address or phone number."]
        if errors:
            raise ValidationError(errors)
        for f in YOUTH_ONLY:
            data[f] = None
    return data


class RegistrationCreateSchema(_RegistrationFields, PublicFormSchema):
    @validates_schema
    def _rules(self, data, **kwargs):
        validate_registration(dict(data))

    @post_load
    def _normalize(self, data, **kwargs):
        return validate_registration(data)


class RegistrationSchema(_RegistrationFields, AdminSchema):
    status = Choice(m.REGISTRATION_STATUSES, load_default="pending")
    admin_notes = S(5000)
    program_title = fields.Function(lambda r: r.program.title if r.program else None, dump_only=True)

    @validates_schema
    def _rules(self, data, **kwargs):
        validate_registration(dict(data))

    @post_load
    def _normalize(self, data, **kwargs):
        return validate_registration(data)


# ---------------------------------------------------------------------------
# Public forms
# ---------------------------------------------------------------------------
class _VolunteerFields:
    name = Req(120)
    email = Email(required=True)
    phone = Phone()
    roles = fields.List(Choice(m.VOLUNTEER_ROLES), required=True,
                        validate=validate.Length(min=1, error="Choose at least one role."))
    availability = S(2000)
    message = S(5000)

    @post_load
    def _dedupe_roles(self, data, **kwargs):
        if "roles" in data:
            data["roles"] = list(dict.fromkeys(data["roles"]))
        return data


class VolunteerCreateSchema(_VolunteerFields, PublicFormSchema):
    pass


class VolunteerSchema(_VolunteerFields, AdminSchema):
    pass


class _ContactFields:
    type = Choice(m.CONTACT_TYPES, load_default="general")
    name = Req(120)
    email = Email(required=True)
    organization = S(200)
    subject = S(200)
    message = Req(5000)


class ContactCreateSchema(_ContactFields, PublicFormSchema):
    pass


class ContactMessageSchema(_ContactFields, AdminSchema):
    is_read = fields.Boolean(load_default=False)


class _ResearchInquiryFields:
    name = Req(120)
    institution = Req(200)
    role = S(150)
    email = Email(required=True)
    area_of_interest = S(300)
    message = S(5000)


class ResearchInquiryCreateSchema(_ResearchInquiryFields, PublicFormSchema):
    pass


class ResearchPartnerInquirySchema(_ResearchInquiryFields, AdminSchema):
    is_read = fields.Boolean(load_default=False)


class _ResearchInterestFields:
    name = Req(120)
    email_or_phone = Req(255)
    neighborhood = S(100)
    consent_to_contact = fields.Boolean(required=True)

    @validates_schema
    def _check(self, data, **kwargs):
        errors = {}
        v = data.get("email_or_phone")
        if v:
            try:
                if "@" in v:
                    if not _is_email(v):
                        raise ValidationError("x")
                else:
                    _phone(v)
            except ValidationError:
                errors["email_or_phone"] = ["Enter a valid email address or phone number."]
        if data.get("consent_to_contact") is not True:
            errors["consent_to_contact"] = ["Please agree to be contacted so we can reach you."]
        if errors:
            raise ValidationError(errors)


class ResearchInterestCreateSchema(_ResearchInterestFields, PublicFormSchema):
    pass


class ResearchInterestSchema(_ResearchInterestFields, AdminSchema):
    pass


class DonationCheckoutSchema(PublicFormSchema):
    amount = fields.Decimal(required=True, places=2, as_string=True,
                            validate=validate.Range(min=0, min_inclusive=False))
    recurring = fields.Boolean(load_default=False)
    designation = Choice(m.DONATION_DESIGNATIONS, load_default="general")
    donor_name = S(120)
    donor_email = Email()


# ---------------------------------------------------------------------------
# Donations (admin)
# ---------------------------------------------------------------------------
class DonationSchema(AdminSchema):
    stripe_session_id = S(255)
    stripe_payment_intent_id = S(255)
    stripe_subscription_id = S(255)
    stripe_invoice_id = S(255)
    stripe_customer_id = S(255)
    amount_cents = fields.Integer(required=True, validate=validate.Range(min=0))
    currency = S(3, load_default="usd")
    recurring = fields.Boolean(load_default=False)
    designation = Choice(m.DONATION_DESIGNATIONS, load_default="general")
    donor_name = S(120)
    donor_email = Email()
    status = Choice(m.DONATION_STATUSES, load_default="pending")
    subscription_status = S(30)
    receipt_sent_at = UTCDateTime(dump_only=True)


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
class NewsPostSchema(AdminSchema):
    title = Req(200)
    slug = ProgramSchema._declared_fields["slug"]
    body = S(200000)
    cover_image_url = Url()
    category = Choice(m.NEWS_CATEGORIES, load_default="community")
    is_published = fields.Boolean(load_default=False)
    published_at = UTCDateTime(allow_none=True)
    excerpt = fields.Method("get_excerpt", dump_only=True)

    def get_excerpt(self, obj):
        text = html.unescape(strip_tags(obj.body))
        text = re.sub(r"\s+", " ", text)
        return text if len(text) <= 220 else text[:217].rsplit(" ", 1)[0] + "…"

    @post_load
    def _defaults(self, data, **kwargs):
        if "body" in data and data["body"] is None:
            data["body"] = ""
        return data


class TeamMemberSchema(AdminSchema):
    name = Req(120)
    role_title = S(150)
    bio = S(10000)
    photo_url = Url()
    group = Choice(m.TEAM_GROUPS, load_default="staff")
    sort_order = fields.Integer(load_default=0)


class PartnerSchema(AdminSchema):
    name = Req(150)
    type = Choice(m.PARTNER_TYPES, load_default="community")
    logo_url = Url()
    website_url = Url()
    sort_order = fields.Integer(load_default=0)


class ImpactStatSchema(AdminSchema):
    label = Req(150)
    value = Req(50)
    sort_order = fields.Integer(load_default=0)


class SiteSettingSchema(AdminSchema):
    key = fields.String(required=True, validate=validate.Regexp(
        r"^[a-z0-9_.\-]{1,100}$", error="Use lowercase letters, numbers, _ . -"))
    value = fields.String(load_default="", validate=validate.Length(max=20000))
    is_public = fields.Boolean(load_default=True)

    @post_load
    def _defaults(self, data, **kwargs):
        if data.get("value") is None:
            data["value"] = ""
        return data


class SiteImageSchema(AdminSchema):
    slot_key = fields.String(required=True, validate=validate.Regexp(
        r"^[a-z0-9\-]{1,100}$", error="Use lowercase letters, numbers and dashes."))
    image_url = Url()
    alt_text = S(300)

    @post_load
    def _defaults(self, data, **kwargs):
        for k in ("image_url", "alt_text"):
            if k in data and data[k] is None:
                data[k] = ""
        return data


class GalleryPhotoSchema(AdminSchema):
    image_url = Url(required=True)
    caption = S(500)
    division = Choice(m.GALLERY_DIVISIONS, load_default="community")
    alt_text = Req(300)
    consent_confirmed = fields.Boolean(load_default=False)
    is_published = fields.Boolean(load_default=False)
    sort_order = fields.Integer(load_default=0)

    @validates_schema
    def _consent(self, data, **kwargs):
        if data.get("is_published") and not data.get("consent_confirmed"):
            raise ValidationError({"is_published": [
                "Confirm photo consent (consent_confirmed) before publishing."]})


class ResearchReferenceSchema(AdminSchema):
    title = Req(300)
    authors = S(500)
    year = fields.Integer(allow_none=True, validate=validate.Range(min=1800, max=2100))
    url = Url()
    summary = S(10000)
    is_verified = fields.Boolean(load_default=False)


# ---------------------------------------------------------------------------
# Admin users
# ---------------------------------------------------------------------------
class UserSchema(AdminSchema):
    email = Email(required=True)
    name = S(120, load_default="")
    is_active = fields.Boolean(load_default=True)
    last_login_at = UTCDateTime(dump_only=True)
    # Write-only; never dumped. Required on create (checked in the route).
    password = fields.String(load_only=True, allow_none=True,
                             validate=validate.Length(min=10, max=200,
                                                      error="Password must be 10–200 characters."))

    @post_load
    def _defaults(self, data, **kwargs):
        if data.get("name") is None:
            data["name"] = ""
        return data


class LoginSchema(PublicFormSchema):
    email = fields.String(required=True, validate=validate.Length(max=255))
    password = fields.String(required=True, validate=validate.Length(max=200))
