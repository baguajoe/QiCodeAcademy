"""Transactional emails for form submissions, registration status changes and donations.

Every user-supplied value is HTML-escaped in the HTML part. Admin notifications
contain only what's needed to triage; full details live in the admin panel.
"""
from flask import current_app
from markupsafe import escape
from sqlalchemy import select

from ..commands import TAX_STATUS
from ..extensions import db
from .email import send_email

DIVISION_LABELS = {"youth": "Youth", "senior": "Seniors", "research": "Research",
                   "general": "Where it's needed most", "intergenerational": "Intergenerational",
                   "community": "Community"}
ROLE_LABELS = {"coding_mentor": "Coding mentor", "wellness_assistant": "Wellness assistant",
               "event_help": "Event help", "senior_tech_tutor": "Tech tutor for seniors"}


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def _org():
    return current_app.config.get("ORG_NAME", "Qi Code Academy")


def _site():
    return current_app.config.get("SITE_URL", "")


def _setting(key, default=""):
    from ..models import SiteSetting
    row = db.session.scalar(select(SiteSetting).where(SiteSetting.key == key))
    return row.value if row and row.value else default


def _admin_recipients():
    raw = current_app.config.get("ADMIN_NOTIFY_EMAIL") or ""
    return [a.strip() for a in raw.split(",") if a.strip()]


def _render(greeting, paragraphs, details=None, footer=None):
    """Build (text, html) from plain-text parts. Values are escaped for HTML."""
    details = [(k, v) for k, v in (details or []) if v not in (None, "")]
    text_lines = [greeting, ""]
    for p in paragraphs:
        text_lines += [p, ""]
    if details:
        text_lines += [f"{k}: {v}" for k, v in details] + [""]
    sign = footer or f"— The {_org()} team\n{_site()}"
    text_lines.append(sign)
    text = "\n".join(text_lines)

    rows = "".join(
        f'<tr><td style="padding:4px 12px 4px 0;color:#555;vertical-align:top">{escape(k)}</td>'
        f'<td style="padding:4px 0">{escape(v)}</td></tr>' for k, v in details)
    html = (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.5;'
        'color:#222;max-width:600px">'
        f"<p>{escape(greeting)}</p>"
        + "".join(f"<p>{escape(p)}</p>" for p in paragraphs)
        + (f'<table style="border-collapse:collapse;margin:8px 0 16px">{rows}</table>' if rows else "")
        + f'<p style="color:#555">{escape(sign).replace(chr(10), "<br>")}</p></div>'
    )
    return text, html


def _notify_admin(subject, lines, reply_to=None):
    to = _admin_recipients()
    if not to:
        return False
    text, html = _render("New submission on the website:", [], lines,
                         footer=f"Review it in the admin panel: {_site()}/admin")
    return send_email(to, f"[{_org()}] {subject}", text, html, reply_to=reply_to)


# ---------------------------------------------------------------------------
# Registrations
# ---------------------------------------------------------------------------
def _program_details(program):
    dates = None
    if program.start_date:
        dates = program.start_date.strftime("%B %-d, %Y")
        if program.end_date:
            dates += " – " + program.end_date.strftime("%B %-d, %Y")
    return [("Program", program.title), ("Schedule", program.schedule), ("Dates", dates),
            ("Location", program.location), ("Neighborhood", program.neighborhood),
            ("Cost", program.cost)]


def registration_received(reg):
    program = reg.program
    to = reg.contact_email
    who = reg.guardian_name if reg.type == "youth" else reg.participant_first_name
    if reg.status == "waitlist":
        subject = f"You're on the waitlist: {program.title}"
        body = [f"Thank you for registering {reg.participant_name} for {program.title}. "
                "This program is currently full, so we've added you to the waitlist.",
                "We'll contact you right away if a spot opens up."]
    else:
        subject = f"Registration received: {program.title}"
        body = [f"Thank you for registering {reg.participant_name} for {program.title}! "
                "We've received your registration and will follow up to confirm your spot "
                "and share any details you need before the first session."]
    body.append("Questions? Just reply to this email.")
    if to:
        text, html = _render(f"Hi {who},", body,
                             [("Participant", reg.participant_name)] + _program_details(program))
        send_email(to, subject, text, html, reply_to=current_app.config.get("MAIL_REPLY_TO"))

    _notify_admin(f"New {reg.type} registration ({reg.status}): {program.title}", [
        ("Program", program.title), ("Type", reg.type), ("Status", reg.status),
        ("Participant", reg.participant_name),
        ("Seats left", "unlimited" if program.capacity is None else program.seats_left),
    ])


def registration_confirmed(reg):
    to = reg.contact_email
    if not to:
        return False
    who = reg.guardian_name if reg.type == "youth" else reg.participant_first_name
    text, html = _render(
        f"Hi {who},",
        [f"Good news — {reg.participant_name}'s spot in {reg.program.title} is confirmed!",
         "We look forward to seeing you. Reply to this email if anything changes."],
        [("Participant", reg.participant_name)] + _program_details(reg.program))
    return send_email(to, f"You're confirmed: {reg.program.title}", text, html,
                      reply_to=current_app.config.get("MAIL_REPLY_TO"))


# ---------------------------------------------------------------------------
# Other forms
# ---------------------------------------------------------------------------
def volunteer_received(vol):
    roles = ", ".join(ROLE_LABELS.get(r, r) for r in vol.roles or [])
    text, html = _render(
        f"Hi {vol.name},",
        [f"Thank you for offering to volunteer with {_org()}! We've received your information "
         "and a member of our team will reach out about next steps."],
        [("Roles", roles), ("Availability", vol.availability)])
    send_email(vol.email, f"Thanks for volunteering with {_org()}", text, html)
    _notify_admin(f"New volunteer: {vol.name}", [
        ("Name", vol.name), ("Email", vol.email), ("Phone", vol.phone), ("Roles", roles),
        ("Availability", vol.availability), ("Message", vol.message)], reply_to=vol.email)


CONTACT_SUBJECTS = {"general": "Contact message", "guest_instructor": "Guest instructor inquiry",
                    "partner": "Partner / sponsor inquiry"}


def contact_received(msg):
    kind = CONTACT_SUBJECTS.get(msg.type, "Contact message")
    text, html = _render(
        f"Hi {msg.name},",
        [f"Thanks for contacting {_org()}. We've received your message and will get back to you soon."],
        [("Subject", msg.subject), ("Your message", msg.message)])
    send_email(msg.email, f"We received your message — {_org()}", text, html)
    _notify_admin(f"{kind}: {msg.subject or msg.name}", [
        ("Type", kind), ("Name", msg.name), ("Email", msg.email),
        ("Organization", msg.organization), ("Subject", msg.subject), ("Message", msg.message)],
        reply_to=msg.email)


def research_inquiry_received(inq):
    text, html = _render(
        f"Hi {inq.name},",
        [f"Thank you for your interest in research partnership with {_org()}. "
         "We'll review your note and follow up by email."],
        [("Institution", inq.institution), ("Area of interest", inq.area_of_interest)])
    send_email(inq.email, f"Research partnership inquiry received — {_org()}", text, html)
    _notify_admin(f"Research partnership inquiry: {inq.institution}", [
        ("Name", inq.name), ("Institution", inq.institution), ("Role", inq.role),
        ("Email", inq.email), ("Area of interest", inq.area_of_interest),
        ("Message", inq.message)], reply_to=inq.email)


def research_interest_received(ri):
    if "@" in ri.email_or_phone:
        text, html = _render(
            f"Hi {ri.name},",
            ["Thank you for your interest in future research at "
             f"{_org()}. There are no active studies right now; we'll contact you if an "
             "opportunity becomes available. You can ask us to remove your information at "
             "any time by replying to this email."])
        send_email(ri.email_or_phone, f"Thanks for your interest — {_org()}", text, html)
    _notify_admin("New research interest sign-up", [
        ("Name", ri.name), ("Neighborhood", ri.neighborhood)])


# ---------------------------------------------------------------------------
# Senior Wellness Day
# ---------------------------------------------------------------------------
WELLNESS_ACTIVITY_LABELS = {
    "tai_chi_baguazhang": "Tai Chi and Baguazhang", "chair_yoga_meditation": "Chair yoga and meditation",
    "massage_acupressure": "Chair massage and acupressure", "strength_balance": "Strength and balance",
    "painting_sewing": "Painting and sewing", "wellness_education": "Wellness education",
    "food_social": "Food and social time"}
WELLNESS_PARTICIPATION_LABELS = {
    "practitioner": "Practitioner", "instructor": "Instructor", "arts_crafts": "Arts and crafts",
    "resource_table": "Community resource table", "food": "Food or refreshments", "volunteer": "Volunteer",
    "sponsor": "Sponsor"}
CONTACT_METHOD_LABELS = {"email": "Email", "phone": "Phone call", "text": "Text message"}


def _labels(values, mapping):
    return ", ".join(mapping.get(v, v) for v in values or [])


def wellness_interest_received(row):
    activities = _labels(row.activities, WELLNESS_ACTIVITY_LABELS)
    if row.email:
        text, html = _render(
            f"Hi {row.name},",
            ["Thank you for joining the interest list for Senior Wellness Day, a free day of movement, care, "
             "creativity, and community for older adults in Boston.",
             "We're planning it for spring 2027. We'll be in touch when the date and location are set.",
             "You can ask us to remove your information at any time by replying to this email."],
            [("Activities you're interested in", activities)])
        send_email(row.email, f"You're on the Senior Wellness Day interest list — {_org()}", text, html,
                   reply_to=current_app.config.get("MAIL_REPLY_TO"))
    # Like research interest: no contact details in email; they're in the admin panel.
    _notify_admin("Senior Wellness Day: new interest sign-up", [
        ("Name", row.name), ("Neighborhood", row.neighborhood), ("Activities", activities),
        ("Signing up for", "A family member or friend" if row.signing_up_for == "someone_else" else
         "Themselves" if row.signing_up_for == "myself" else None),
        ("Preferred contact", CONTACT_METHOD_LABELS.get(row.contact_method))])


def wellness_partner_received(row):
    types = _labels(row.participation_types, WELLNESS_PARTICIPATION_LABELS)
    text, html = _render(
        f"Hi {row.name},",
        ["Thank you for offering to be part of Senior Wellness Day! We'll review your submission and be in "
         "touch as plans come together.",
         "Please note that submitting the form does not confirm your participation."],
        [("Organization", row.organization), ("Participating as", types)])
    send_email(row.email, f"Senior Wellness Day: we received your submission — {_org()}", text, html,
               reply_to=current_app.config.get("MAIL_REPLY_TO"))
    license_info = " ".join(v for v in (row.license_type, row.license_number) if v) or None
    _notify_admin(f"Senior Wellness Day: {types} — {row.display_name}", [
        ("Name", row.name), ("Organization", row.organization), ("Email", row.email), ("Phone", row.phone),
        ("Website / social", row.website_or_social), ("Participating as", types), ("Offer", row.offer_description),
        ("License", license_info), ("Liability insurance", row.has_insurance), ("Volunteer or fee", row.compensation),
        ("Typical rate", row.typical_rate)], reply_to=row.email)


# ---------------------------------------------------------------------------
# Donations
# ---------------------------------------------------------------------------
def donation_thank_you(donation):
    if not donation.donor_email:
        return False
    amount = f"${donation.amount_cents / 100:,.2f}"
    legal = current_app.config.get("ORG_LEGAL_NAME", "Qi Code Academy, Inc.")
    tax_status = _setting("tax_status", TAX_STATUS)
    kind = "monthly gift" if donation.recurring else "gift"
    paragraphs = [f"Thank you for your {kind} of {amount} to {_org()}. Your support helps us "
                  "serve youth and seniors across Boston."]
    if donation.recurring:
        paragraphs.append("Your gift will repeat monthly. To change or cancel it, reply to this "
                          "email and we'll take care of it.")
    paragraphs.append(tax_status)
    paragraphs.append("Please keep this email for your records.")
    text, html = _render(
        f"Dear {donation.donor_name or 'friend'},", paragraphs,
        [("Organization", legal), ("Amount", amount),
         ("Frequency", "Monthly" if donation.recurring else "One-time"),
         ("Designation", DIVISION_LABELS.get(donation.designation, donation.designation)),
         ("Date", donation.created_at.strftime("%B %-d, %Y") if donation.created_at else None),
         ("Reference", donation.stripe_invoice_id or donation.stripe_session_id)])
    return send_email(donation.donor_email, f"Thank you for your gift to {_org()}", text, html,
                      reply_to=current_app.config.get("MAIL_REPLY_TO"))
