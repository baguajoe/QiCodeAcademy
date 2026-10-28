"""Senior Wellness Day: senior interest list, partner/vendor/volunteer form, public lineup, admin."""
import re
from pathlib import Path

import pytest

from api.models import WellnessDayInterest, WellnessDayPartner

from .test_flask_admin import _login

ROOT = Path(__file__).resolve().parents[1]

INTEREST = {"name": "Rose Brown", "email": "rose@example.org", "neighborhood": "Dorchester",
            "activities": ["tai_chi_baguazhang", "painting_sewing"], "contact_method": "email",
            "signing_up_for": "myself", "consent_to_contact": True}

PARTNER = {"name": "Ana Silva", "organization": "Silva Bodywork", "email": "ana@example.org",
           "participation_types": ["practitioner"], "offer_description": "Seated chair massage, 10-minute sessions.",
           "license_type": "Massachusetts massage therapist", "license_number": "MT-12345",
           "has_insurance": "yes", "compensation": "volunteer", "setup_needs": ["chairs", "quiet_space"],
           "availability": ["saturdays"], "agrees_no_sales": True, "agrees_not_confirmed": True}


def _partner(db, **kw):
    p = WellnessDayPartner(**{**{k: v for k, v in PARTNER.items()}, **kw})
    db.session.add(p)
    db.session.commit()
    return p


# ---------------------------------------------------------------------------
# Senior interest form
# ---------------------------------------------------------------------------
def test_interest_signup_stores_and_emails(client, db, outbox, app):
    app.config["ADMIN_NOTIFY_EMAIL"] = "staff@example.org"
    res = client.post("/api/wellness-day/interest", json=INTEREST)
    assert res.status_code == 201
    assert res.get_json() == {"ok": True, "message": "Thank you! We'll be in touch when the date is set."}
    row = db.session.query(WellnessDayInterest).one()
    assert row.activities == ["tai_chi_baguazhang", "painting_sewing"] and row.consent_to_contact is True
    assert {m.to[0] for m in outbox} == {"rose@example.org", "staff@example.org"}
    admin_mail = next(m for m in outbox if m.to == ["staff@example.org"])
    assert "rose@example.org" not in admin_mail.text  # contact details stay in the admin panel


def test_interest_phone_only_sends_no_confirmation(client, db, outbox):
    payload = {**INTEREST, "email": "", "phone": "617-555-0100", "contact_method": "text"}
    assert client.post("/api/wellness-day/interest", json=payload).status_code == 201
    assert not [m for m in outbox if "interest list" in m.subject]  # no address to confirm to


@pytest.mark.parametrize("change, field", [
    ({"name": ""}, "name"),
    ({"email": "", "phone": ""}, "email"),
    ({"email": "not-an-email"}, "email"),
    ({"consent_to_contact": False}, "consent_to_contact"),
    ({"neighborhood": "Atlantis"}, "neighborhood"),
    ({"activities": ["skydiving"]}, "activities"),
    ({"contact_method": "phone", "phone": ""}, "phone"),
    ({"signing_up_for": "the cat"}, "signing_up_for"),
])
def test_interest_validation(client, db, change, field):
    res = client.post("/api/wellness-day/interest", json={**INTEREST, **change})
    assert res.status_code == 400 and field in res.get_json()["errors"]
    assert db.session.query(WellnessDayInterest).count() == 0


def test_interest_never_stores_health_or_age(client, db):
    cols = {c.name for c in WellnessDayInterest.__table__.columns}
    for banned in ("age", "date_of_birth", "dob", "birth", "health", "condition", "medication", "medical",
                   "diagnosis", "comfort_notes"):
        assert not any(banned in c for c in cols), banned
    # Extra keys are ignored, not stored.
    res = client.post("/api/wellness-day/interest", json={**INTEREST, "age": 82, "medications": "x"})
    assert res.status_code == 201


def test_interest_honeypot(client, db, outbox):
    res = client.post("/api/wellness-day/interest", json={**INTEREST, "website": "spam.example"})
    assert res.status_code == 201 and res.get_json()["ok"] is True
    assert db.session.query(WellnessDayInterest).count() == 0 and outbox == []


# ---------------------------------------------------------------------------
# Partners / vendors / volunteers form
# ---------------------------------------------------------------------------
def test_partner_submission_defaults_private(client, db, outbox, app):
    app.config["ADMIN_NOTIFY_EMAIL"] = "staff@example.org"
    res = client.post("/api/wellness-day/partners", json={**PARTNER, "typical_rate": "40/hour"})
    assert res.status_code == 201
    assert res.get_json()["message"] == ("Thank you! We'll review your submission and be in touch as plans "
                                         "come together.")
    p = db.session.query(WellnessDayPartner).one()
    assert p.status == "new" and p.show_publicly is False
    assert p.typical_rate is None  # only kept when they chose "paid"
    admin_mail = next(m for m in outbox if m.to == ["staff@example.org"])
    assert admin_mail.reply_to == "ana@example.org"


def test_partner_paid_rate_kept_and_none_setup_dropped(client, db):
    payload = {**PARTNER, "participation_types": ["arts_crafts"], "license_type": "", "license_number": "",
               "compensation": "paid", "typical_rate": "Open to discussion", "setup_needs": ["none", "table"]}
    assert client.post("/api/wellness-day/partners", json=payload).status_code == 201
    p = db.session.query(WellnessDayPartner).one()
    assert p.typical_rate == "Open to discussion" and p.setup_needs == ["table"]


@pytest.mark.parametrize("change, field", [
    ({"name": ""}, "name"),
    ({"email": ""}, "email"),
    ({"participation_types": []}, "participation_types"),
    ({"participation_types": ["juggler"]}, "participation_types"),
    ({"offer_description": ""}, "offer_description"),
    ({"offer_description": "x" * 601}, "offer_description"),
    ({"license_number": ""}, "license_number"),          # practitioner needs a license
    ({"license_type": ""}, "license_type"),
    ({"agrees_no_sales": False}, "agrees_no_sales"),
    ({"agrees_not_confirmed": False}, "agrees_not_confirmed"),
    ({"has_insurance": "maybe"}, "has_insurance"),
    ({"availability": ["mondays"]}, "availability"),
])
def test_partner_validation(client, db, change, field):
    res = client.post("/api/wellness-day/partners", json={**PARTNER, **change})
    assert res.status_code == 400 and field in res.get_json()["errors"], res.get_json()
    assert db.session.query(WellnessDayPartner).count() == 0


def test_non_practitioner_needs_no_license(client, db):
    payload = {**PARTNER, "participation_types": ["volunteer", "food"], "license_type": None, "license_number": None}
    assert client.post("/api/wellness-day/partners", json=payload).status_code == 201


def test_partner_honeypot(client, db):
    res = client.post("/api/wellness-day/partners", json={**PARTNER, "website": "http://spam"})
    assert res.status_code == 201 and db.session.query(WellnessDayPartner).count() == 0


def test_partner_social_link_is_not_the_honeypot(client, db):
    # The real "website or social link" field is `website_or_social`; `website` stays the honeypot.
    res = client.post("/api/wellness-day/partners", json={**PARTNER, "website_or_social": "instagram.com/silva"})
    assert res.status_code == 201
    assert db.session.query(WellnessDayPartner).one().website_or_social == "instagram.com/silva"


def test_both_forms_rate_limited(rate_limited_app):
    c = rate_limited_app.test_client()
    for _ in range(2):
        assert c.post("/api/wellness-day/interest", json=INTEREST).status_code == 201
    assert c.post("/api/wellness-day/interest", json=INTEREST).status_code == 429
    for _ in range(2):
        assert c.post("/api/wellness-day/partners", json=PARTNER).status_code == 201
    assert c.post("/api/wellness-day/partners", json=PARTNER).status_code == 429


# ---------------------------------------------------------------------------
# Public lineup
# ---------------------------------------------------------------------------
def test_lineup_only_confirmed_and_public(client, db):
    assert client.get("/api/wellness-day/lineup").get_json() == {"items": []}
    _partner(db, organization="Shown Org", status="confirmed", show_publicly=True,
             participation_types=["practitioner", "volunteer"])
    _partner(db, name="Solo Person", organization=None, email="solo@example.org", status="confirmed",
             show_publicly=True, participation_types=["instructor"])
    _partner(db, organization="Confirmed But Private", status="confirmed", show_publicly=False)
    _partner(db, organization="Public But New", status="new", show_publicly=True)
    _partner(db, organization="Contacted Org", status="contacted", show_publicly=True)
    _partner(db, organization="Declined Org", status="declined", show_publicly=True)
    items = client.get("/api/wellness-day/lineup").get_json()["items"]
    assert items == [{"name": "Shown Org", "participation_types": ["practitioner", "volunteer"]},
                     {"name": "Solo Person", "participation_types": ["instructor"]}]
    # Only the display name and types: never contact details, licenses, notes, or descriptions.
    assert all(set(i) == {"name", "participation_types"} for i in items)


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------
def test_admin_interest_list_filters_summary_and_csv(client, db, auth_headers):
    client.post("/api/wellness-day/interest", json=INTEREST)
    client.post("/api/wellness-day/interest", json={**INTEREST, "name": "Lee", "neighborhood": "Roxbury",
                                                    "activities": ["food_social"]})
    client.post("/api/wellness-day/interest", json={**INTEREST, "name": "Kim", "neighborhood": None,
                                                    "activities": ["painting_sewing"]})
    assert client.get("/api/admin/wellness-day-interest").status_code == 401
    res = client.get("/api/admin/wellness-day-interest?neighborhood=Roxbury", headers=auth_headers).get_json()
    assert [r["name"] for r in res["items"]] == ["Lee"]
    res = client.get("/api/admin/wellness-day-interest?activity=painting_sewing", headers=auth_headers).get_json()
    assert sorted(r["name"] for r in res["items"]) == ["Kim", "Rose Brown"]
    assert client.get("/api/admin/wellness-day-interest?activity=%25", headers=auth_headers).status_code == 400

    s = client.get("/api/admin/wellness-day/summary", headers=auth_headers).get_json()
    assert s["interest_total"] == 3
    assert s["interest_by_activity"]["painting_sewing"] == 2 and s["interest_by_activity"]["food_social"] == 1
    assert s["interest_by_neighborhood"]["Dorchester"] == 1 and s["interest_by_neighborhood"]["not_given"] == 1

    csv = client.get("/api/admin/wellness-day-interest/export.csv?neighborhood=Dorchester", headers=auth_headers)
    lines = csv.get_data(as_text=True).lstrip("﻿").strip().splitlines()
    assert lines[0].startswith("id,created_at_utc,name,email,phone,neighborhood,activities")
    assert len(lines) == 2 and "Rose Brown" in lines[1]


def test_admin_partners_filters_lineup_and_csv(client, db, auth_headers):
    _partner(db, organization="A Org", status="confirmed", show_publicly=True)
    _partner(db, organization="B Org", status="new", participation_types=["sponsor"], license_type=None,
             license_number=None)
    res = client.get("/api/admin/wellness-day-partners?participation_type=sponsor", headers=auth_headers).get_json()
    assert [r["organization"] for r in res["items"]] == ["B Org"]
    res = client.get("/api/admin/wellness-day-partners?status=confirmed", headers=auth_headers).get_json()
    assert [r["organization"] for r in res["items"]] == ["A Org"]
    s = client.get("/api/admin/wellness-day/summary", headers=auth_headers).get_json()
    assert [p["display_name"] for p in s["confirmed_lineup"]] == ["A Org"]
    assert s["partners_by_status"] == {"new": 1, "contacted": 0, "confirmed": 1, "declined": 0}

    b = db.session.query(WellnessDayPartner).filter_by(organization="B Org").one()
    res = client.patch(f"/api/admin/wellness-day-partners/{b.id}", headers=auth_headers,
                       json={"status": "confirmed", "show_publicly": True, "admin_notes": "Called 3/2"})
    assert res.status_code == 200
    assert [i["name"] for i in client.get("/api/wellness-day/lineup").get_json()["items"]] == ["A Org", "B Org"]
    # Admin edits keep the practitioner license rule.
    a = db.session.query(WellnessDayPartner).filter_by(organization="A Org").one()
    assert client.patch(f"/api/admin/wellness-day-partners/{a.id}", headers=auth_headers,
                        json={"license_number": ""}).status_code == 400

    csv = client.get("/api/admin/wellness-day-partners/export.csv?participation_type=sponsor", headers=auth_headers)
    text = csv.get_data(as_text=True)
    assert "B Org" in text and "A Org" not in text and "admin_notes" in text.splitlines()[0]


def test_dashboard_counts(client, db, auth_headers):
    client.post("/api/wellness-day/interest", json=INTEREST)
    _partner(db)
    d = client.get("/api/admin/dashboard", headers=auth_headers).get_json()
    assert d["wellness_interest_total"] == 1 and d["wellness_partners_new"] == 1


# ---------------------------------------------------------------------------
# Flask-Admin
# ---------------------------------------------------------------------------
def test_flask_admin_views(client, db, admin_user):
    client.post("/api/wellness-day/interest", json=INTEREST)
    _partner(db, organization="Confirmed Co", status="confirmed")
    _partner(db, organization="New Co", status="new")
    _login(client)
    page = client.get("/flask-admin/fa_wellness_day_interest/").get_data(as_text=True)
    assert "Total sign-ups: 1" in page and "Painting and sewing" in page
    assert client.get("/flask-admin/fa_wellness_day_interest/export/csv/").status_code == 200
    assert client.get("/flask-admin/fa_wellness_day_partners/").status_code == 200
    assert client.get("/flask-admin/fa_wellness_day_partners/new/").status_code == 200
    assert client.get("/flask-admin/fa_wellness_day_partners/export/csv/").status_code == 200
    lineup = client.get("/flask-admin/fa_wellness_day_lineup/").get_data(as_text=True)
    assert "Confirmed Co" in lineup and "New Co" not in lineup
    # Filters by participation type (custom JSON-list filter) and status are offered.
    page = client.get("/flask-admin/fa_wellness_day_partners/").get_data(as_text=True)
    assert "Participation type" in page and "Status" in page


def test_flask_admin_json_list_filter(app, db):
    from api.admin_panel import JsonListContainsFilter
    _partner(db, organization="Sponsor Co", participation_types=["sponsor"], license_type=None, license_number=None)
    _partner(db, organization="Massage Co")
    f = JsonListContainsFilter(WellnessDayPartner.participation_types, "Type", options=[("sponsor", "Sponsor")])
    q = db.session.query(WellnessDayPartner)
    assert [p.organization for p in f.apply(q, "sponsor")] == ["Sponsor Co"]
    assert f.apply(q, "%").count() == 2  # unknown values are ignored, never used as a LIKE pattern


# ---------------------------------------------------------------------------
# Settings + content rules
# ---------------------------------------------------------------------------
def test_settings_seeded(client, db):
    from api.commands import seed_settings
    seed_settings()
    db.session.commit()
    s = client.get("/api/settings").get_json()
    assert s["wellness_day_status"] == "Coming spring 2027"
    assert s["wellness_day_date"] == "" and s["wellness_day_location"] == ""


def test_wellness_page_has_no_donations_or_dollar_amounts():
    page = (ROOT / "src/front/js/pages/WellnessDay.js").read_text()
    assert "/donate" not in page and "btn-donate" not in page and "$" not in re.sub(r"\$\{", "", page)
    import json
    en = json.loads((ROOT / "src/front/locales/en.json").read_text())["wellnessDay"]

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                yield from walk(x)
        elif isinstance(v, list):
            for x in v:
                yield from walk(x)
        else:
            yield v
    copy = " ".join(walk(en))
    assert "$" not in copy and not re.search(r"\bdonat", copy, re.I)
    assert "Participants should consult their healthcare provider before starting a new exercise program." in copy
