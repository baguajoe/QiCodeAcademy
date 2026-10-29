"""Senior Wellness Day: senior interest list, partner/vendor/volunteer form, public lineup, admin."""
import re
from pathlib import Path

import pytest

from api.models import WellnessDayInterest, WellnessDayPartner

from .test_flask_admin import _login

ROOT = Path(__file__).resolve().parents[1]

INTEREST = {"name": "Rose Brown", "email": "rose@example.org", "neighborhood": "Dorchester",
            "activities": ["tai_chi_baguazhang", "painting"], "contact_method": "email",
            "signing_up_for": "myself", "consent_to_contact": True}

AGREEMENTS = {"agrees_not_confirmed": True, "agrees_respectful": True, "agrees_permits": True,
              "agrees_restricted_products": True}
PARTNER = {"name": "Ana Silva", "organization": "Silva Bodywork", "email": "ana@example.org",
           "participation_types": ["practitioner_massage"], "offer_description": "Seated chair massage, 10-minute sessions.",
           "license_type": "Massachusetts massage therapist", "license_number": "MT-12345",
           "has_insurance": "yes", "compensation": "volunteer", "setup_needs": ["chairs", "quiet_space"],
           "availability": ["saturdays"], **AGREEMENTS}
VENDOR = {"name": "Kay Mensah", "organization": "Mensah Beads", "email": "kay@example.org",
          "participation_types": ["vendor"], "offer_description": "A table of handmade jewelry.",
          "vendor_products": "Beaded necklaces and bracelets", "vendor_category": "jewelry",
          "vendor_price_range": "Most items under twenty", "setup_needs": ["table", "tent"], **AGREEMENTS}


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
    assert row.activities == ["tai_chi_baguazhang", "painting"] and row.consent_to_contact is True
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


def test_interest_senior_maker_fields(client, db, outbox, app):
    app.config["ADMIN_NOTIFY_EMAIL"] = "staff@example.org"
    payload = {**INTEREST, "activities": ["acupuncture", "marketplace"], "wants_to_sell": True,
               "sell_items": "Quilts and knitted hats", "needs_table": "yes"}
    assert client.post("/api/wellness-day/interest", json=payload).status_code == 201
    row = db.session.query(WellnessDayInterest).one()
    assert row.wants_to_sell is True and row.sell_items == "Quilts and knitted hats" and row.needs_table == "yes"
    assert row.activities == ["acupuncture", "marketplace"]
    admin_mail = next(m for m in outbox if m.to == ["staff@example.org"])
    assert "Quilts and knitted hats" in admin_mail.text


def test_interest_seller_details_dropped_when_not_selling(client, db):
    payload = {**INTEREST, "wants_to_sell": False, "sell_items": "Paintings", "needs_table": "no"}
    assert client.post("/api/wellness-day/interest", json=payload).status_code == 201
    row = db.session.query(WellnessDayInterest).one()
    assert row.wants_to_sell is False and row.sell_items is None and row.needs_table is None


@pytest.mark.parametrize("change, field", [
    ({"wants_to_sell": True, "sell_items": ""}, "sell_items"),
    ({"wants_to_sell": True, "sell_items": "Art", "needs_table": "maybe"}, "needs_table"),
    ({"wants_to_sell": True, "sell_items": "x" * 301}, "sell_items"),
])
def test_interest_seller_validation(client, db, change, field):
    res = client.post("/api/wellness-day/interest", json={**INTEREST, **change})
    assert res.status_code == 400 and field in res.get_json()["errors"]


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
    payload = {**PARTNER, "participation_types": ["painting"], "license_type": "", "license_number": "",
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
    ({"agrees_not_confirmed": False}, "agrees_not_confirmed"),
    ({"agrees_respectful": False}, "agrees_respectful"),
    ({"agrees_permits": False}, "agrees_permits"),
    ({"agrees_restricted_products": False}, "agrees_restricted_products"),
    ({"participation_types": ["practitioner"]}, "participation_types"),  # old combined key is gone
    ({"vendor_category": "cars"}, "vendor_category"),
    ({"has_insurance": "maybe"}, "has_insurance"),
    ({"availability": ["mondays"]}, "availability"),
])
def test_partner_validation(client, db, change, field):
    res = client.post("/api/wellness-day/partners", json={**PARTNER, **change})
    assert res.status_code == 400 and field in res.get_json()["errors"], res.get_json()
    assert db.session.query(WellnessDayPartner).count() == 0


@pytest.mark.parametrize("ptype", ["practitioner_massage", "practitioner_acupuncture", "practitioner_bodywork"])
def test_every_practitioner_type_needs_a_license(client, db, ptype):
    payload = {**PARTNER, "participation_types": ["volunteer", ptype], "license_type": "", "license_number": ""}
    res = client.post("/api/wellness-day/partners", json=payload)
    assert res.status_code == 400
    errors = res.get_json()["errors"]
    assert {"license_type", "license_number"} <= set(errors)
    assert "Massachusetts-licensed" in " ".join(errors["license_number"])


def test_acupuncturist_with_license_accepted(client, db):
    payload = {**PARTNER, "participation_types": ["practitioner_acupuncture"],
               "license_type": "Massachusetts acupuncture license", "license_number": "AC-777"}
    assert client.post("/api/wellness-day/partners", json=payload).status_code == 201
    p = db.session.query(WellnessDayPartner).one()
    assert p.participation_types == ["practitioner_acupuncture"] and p.license_number == "AC-777"


def test_non_practitioner_needs_no_license(client, db):
    payload = {**PARTNER, "participation_types": ["volunteer", "instructor"], "license_type": None, "license_number": None}
    assert client.post("/api/wellness-day/partners", json=payload).status_code == 201


def test_vendor_submission_stores_vendor_fields(client, db, outbox, app):
    app.config["ADMIN_NOTIFY_EMAIL"] = "staff@example.org"
    assert client.post("/api/wellness-day/partners", json=VENDOR).status_code == 201
    p = db.session.query(WellnessDayPartner).one()
    assert (p.vendor_products, p.vendor_category, p.vendor_price_range) == (
        "Beaded necklaces and bracelets", "jewelry", "Most items under twenty")
    assert p.setup_needs == ["table", "tent"] and p.license_number is None
    assert p.agrees_respectful and p.agrees_permits and p.agrees_restricted_products and p.agrees_not_confirmed
    admin_mail = next(m for m in outbox if m.to == ["staff@example.org"])
    assert "Beaded necklaces" in admin_mail.text and "Handmade jewelry" in admin_mail.text


@pytest.mark.parametrize("ptype", ["vendor", "food_vendor"])
def test_vendors_must_say_what_they_sell(client, db, ptype):
    res = client.post("/api/wellness-day/partners", json={**VENDOR, "participation_types": [ptype], "vendor_products": ""})
    assert res.status_code == 400 and "vendor_products" in res.get_json()["errors"]


def test_vendor_fields_dropped_for_non_vendors(client, db):
    payload = {**VENDOR, "participation_types": ["volunteer"]}
    assert client.post("/api/wellness-day/partners", json=payload).status_code == 201
    p = db.session.query(WellnessDayPartner).one()
    assert p.vendor_products is None and p.vendor_category is None and p.vendor_price_range is None


def test_old_no_sales_agreement_is_not_required(client, db):
    # The marketplace replaced the old "no product sales" agreement; old clients sending it are ignored.
    assert client.post("/api/wellness-day/partners", json={**PARTNER, "agrees_no_sales": False}).status_code == 201


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
             participation_types=["practitioner_acupuncture", "volunteer"])
    _partner(db, name="Solo Person", organization=None, email="solo@example.org", status="confirmed",
             show_publicly=True, participation_types=["instructor"])
    _partner(db, organization="Confirmed But Private", status="confirmed", show_publicly=False)
    _partner(db, organization="Public But New", status="new", show_publicly=True)
    _partner(db, organization="Contacted Org", status="contacted", show_publicly=True)
    _partner(db, organization="Declined Org", status="declined", show_publicly=True)
    items = client.get("/api/wellness-day/lineup").get_json()["items"]
    assert items == [{"name": "Shown Org", "participation_types": ["practitioner_acupuncture", "volunteer"]},
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
                                                    "activities": ["painting"], "wants_to_sell": True,
                                                    "sell_items": "Watercolors", "needs_table": "no"})
    assert client.get("/api/admin/wellness-day-interest").status_code == 401
    res = client.get("/api/admin/wellness-day-interest?neighborhood=Roxbury", headers=auth_headers).get_json()
    assert [r["name"] for r in res["items"]] == ["Lee"]
    res = client.get("/api/admin/wellness-day-interest?activity=painting", headers=auth_headers).get_json()
    assert sorted(r["name"] for r in res["items"]) == ["Kim", "Rose Brown"]
    assert client.get("/api/admin/wellness-day-interest?activity=%25", headers=auth_headers).status_code == 400
    res = client.get("/api/admin/wellness-day-interest?wants_to_sell=true", headers=auth_headers).get_json()
    assert [r["name"] for r in res["items"]] == ["Kim"] and res["items"][0]["sell_items"] == "Watercolors"

    s = client.get("/api/admin/wellness-day/summary", headers=auth_headers).get_json()
    assert s["interest_total"] == 3
    assert s["interest_by_activity"]["painting"] == 2 and s["interest_by_activity"]["food_social"] == 1
    assert s["interest_by_neighborhood"]["Dorchester"] == 1 and s["interest_by_neighborhood"]["not_given"] == 1
    assert s["senior_makers_total"] == 1

    csv = client.get("/api/admin/wellness-day-interest/export.csv?neighborhood=Dorchester", headers=auth_headers)
    lines = csv.get_data(as_text=True).lstrip("﻿").strip().splitlines()
    assert lines[0].startswith("id,created_at_utc,name,email,phone,neighborhood,activities")
    assert len(lines) == 2 and "Rose Brown" in lines[1]
    assert lines[0].endswith("consent_to_contact,wants_to_sell,sell_items,needs_table")
    makers = client.get("/api/admin/wellness-day-interest/export.csv?wants_to_sell=true", headers=auth_headers)
    rows = makers.get_data(as_text=True).lstrip("\ufeff").strip().splitlines()
    assert len(rows) == 2 and "Kim" in rows[1] and "Watercolors" in rows[1]


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


def test_admin_vendor_category_filter_csv_and_summary(client, db, auth_headers):
    client.post("/api/wellness-day/partners", json=VENDOR)
    client.post("/api/wellness-day/partners", json={**VENDOR, "organization": "Soup Co", "email": "s@example.org",
                                                     "participation_types": ["food_vendor"], "vendor_category": "food",
                                                     "vendor_products": "Soup"})
    _partner(db, organization="Massage Co")
    res = client.get("/api/admin/wellness-day-partners?vendor_category=jewelry", headers=auth_headers).get_json()
    assert [r["organization"] for r in res["items"]] == ["Mensah Beads"]
    res = client.get("/api/admin/wellness-day-partners?participation_type=food_vendor", headers=auth_headers).get_json()
    assert [r["organization"] for r in res["items"]] == ["Soup Co"]
    csv = client.get("/api/admin/wellness-day-partners/export.csv?vendor_category=food", headers=auth_headers)
    lines = csv.get_data(as_text=True).lstrip("\ufeff").strip().splitlines()
    assert "vendor_category" in lines[0] and "vendor_products" in lines[0] and "agrees_permits" in lines[0]
    assert len(lines) == 2 and "Soup Co" in lines[1]
    s = client.get("/api/admin/wellness-day/summary", headers=auth_headers).get_json()
    assert s["vendors_by_category"]["jewelry"] == 1 and s["vendors_by_category"]["food"] == 1
    assert s["partners_by_type"]["vendor"] == 1 and s["partners_by_type"]["practitioner_massage"] == 1


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
    assert "Total sign-ups: 1" in page and "Painting and creative expression" in page
    assert client.get("/flask-admin/fa_wellness_day_interest/export/csv/").status_code == 200
    assert client.get("/flask-admin/fa_wellness_day_partners/").status_code == 200
    assert client.get("/flask-admin/fa_wellness_day_partners/new/").status_code == 200
    assert client.get("/flask-admin/fa_wellness_day_partners/export/csv/").status_code == 200
    lineup = client.get("/flask-admin/fa_wellness_day_lineup/").get_data(as_text=True)
    assert "Confirmed Co" in lineup and "New Co" not in lineup
    # Filters by participation type (custom JSON-list filter) and status are offered.
    page = client.get("/flask-admin/fa_wellness_day_partners/").get_data(as_text=True)
    assert "Participation type" in page and "Status" in page and "Vendor category" in page
    page = client.get("/flask-admin/fa_wellness_day_interest/").get_data(as_text=True)
    assert "Senior makers" in page


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
    assert s["wellness_day_status"] == "Coming May 2027"
    assert s["wellness_day_date"] == "May 2027" and s["wellness_day_location"] == "Boston location to be announced"


def test_old_wellness_day_setting_defaults_are_upgraded(db):
    from api.commands import upgrade_founder_text
    from api.models import SiteSetting
    db.session.add_all([SiteSetting(key="wellness_day_status", value="Coming spring 2027", is_public=True),
                        SiteSetting(key="wellness_day_date", value="", is_public=True),
                        SiteSetting(key="wellness_day_location", value="Grove Hall", is_public=True)])
    db.session.commit()
    upgrade_founder_text()
    values = {r.key: r.value for r in db.session.query(SiteSetting)}
    assert values["wellness_day_status"] == "Coming May 2027" and values["wellness_day_date"] == "May 2027"
    assert values["wellness_day_location"] == "Grove Hall"  # staff edits are kept


def test_old_venue_location_placeholder_is_upgraded(db):
    from api.commands import upgrade_founder_text
    from api.models import SiteSetting
    db.session.add(SiteSetting(key="wellness_day_location", value="BCYF site to be confirmed", is_public=True))
    db.session.commit()
    upgrade_founder_text()
    row = db.session.query(SiteSetting).filter_by(key="wellness_day_location").one()
    assert row.value == "Boston location to be announced"


def test_no_venue_partner_named_for_wellness_day():
    files = [ROOT / "src/api/seo.py", ROOT / "src/api/services/notifications.py",
             *(ROOT / "src/front/locales").glob("*.json"), *(ROOT / "src/front/js").rglob("*.js")]
    assert not [f.name for f in files if "BCYF" in f.read_text()]


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


# ---------------------------------------------------------------------------
# Migration: old combined keys are split into the new ones
# ---------------------------------------------------------------------------
def test_migration_remaps_old_keys():
    import importlib.util

    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    path = next((ROOT / "migrations/versions").glob("a3c9e2f1b7d4_*.py"))
    spec = importlib.util.spec_from_file_location("wd_marketplace_migration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    engine = sa.create_engine("sqlite://")
    meta = sa.MetaData()
    interest = sa.Table("wellness_day_interest", meta, sa.Column("id", sa.Integer, primary_key=True),
                        sa.Column("activities", sa.JSON))
    partners = sa.Table("wellness_day_partners", meta, sa.Column("id", sa.Integer, primary_key=True),
                        sa.Column("participation_types", sa.JSON))
    meta.create_all(engine)
    with engine.begin() as conn:
        conn.execute(interest.insert(), [{"id": 1, "activities": ["massage_acupressure", "food_social"]},
                                         {"id": 2, "activities": ["chair_yoga_meditation"]}])
        conn.execute(partners.insert(), [{"id": 1, "participation_types": ["practitioner", "food", "volunteer"]}])
        with Operations.context(MigrationContext.configure(conn)):
            mod._remap("wellness_day_interest", "activities", mod.ACTIVITY_UP)
            mod._remap("wellness_day_partners", "participation_types", mod.TYPE_UP)
        acts = dict(conn.execute(sa.select(interest.c.id, interest.c.activities)).all())
        types = conn.execute(sa.select(partners.c.participation_types)).scalar_one()
    assert acts == {1: ["chair_massage", "acupressure", "food_social"], 2: ["chair_yoga_meditation"]}
    assert types == ["practitioner_bodywork", "food_vendor", "volunteer"]


def test_final_plan_migration_renames_keys():
    import importlib.util

    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    path = next((ROOT / "migrations/versions").glob("b7e4d2a9c1f3_*.py"))
    spec = importlib.util.spec_from_file_location("wd_final_plan_migration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    engine = sa.create_engine("sqlite://")
    meta = sa.MetaData()
    interest = sa.Table("wellness_day_interest", meta, sa.Column("id", sa.Integer, primary_key=True),
                        sa.Column("activities", sa.JSON))
    partners = sa.Table("wellness_day_partners", meta, sa.Column("id", sa.Integer, primary_key=True),
                        sa.Column("participation_types", sa.JSON), sa.Column("vendor_category", sa.String(30)))
    meta.create_all(engine)
    with engine.begin() as conn:
        conn.execute(interest.insert(), [{"id": 1, "activities": ["painting_sewing", "strength_balance", "acupressure",
                                                                  "wellness_education", "food_social"]}])
        conn.execute(partners.insert(), [{"id": 1, "participation_types": ["arts_crafts", "vendor"], "vendor_category": "art"},
                                         {"id": 2, "participation_types": ["vendor"], "vendor_category": "crafts"},
                                         {"id": 3, "participation_types": ["volunteer"], "vendor_category": None}])
        with Operations.context(MigrationContext.configure(conn)):
            mod.upgrade()
        acts = conn.execute(sa.select(interest.c.activities)).scalar_one()
        rows = conn.execute(sa.select(partners.c.participation_types, partners.c.vendor_category).order_by(partners.c.id)).all()
    assert acts == ["painting", "fall_prevention_balance", "resources", "food_social"]
    assert [tuple(r) for r in rows] == [(["painting", "vendor"], "visual_art"), (["vendor"], "other"), (["volunteer"], None)]


def test_no_sewing_anywhere():
    paths = [*ROOT.glob("src/front/locales/*.json"), *ROOT.glob("src/front/js/**/*.js"), *ROOT.glob("src/api/**/*.py"),
             ROOT / "src/front/img/site/credits.json", ROOT / "IMAGE_CREDITS.md", ROOT / "IMAGE_GUIDE.md", ROOT / "API.md"]
    assert not [p for p in paths if re.search(r"sewing|strength (and|&) balance", p.read_text(), re.I)]


# ---------------------------------------------------------------------------
# Page: event first, forms behind accessible tabs; photos follow the photo rules
# ---------------------------------------------------------------------------
PAGE = ROOT / "src/front/js/pages/WellnessDay.js"


def test_page_forms_are_behind_keyboard_operable_tabs():
    js = PAGE.read_text()
    assert 'role="tablist"' in js and 'role="tab"' in js and 'role="tabpanel"' in js
    assert "aria-selected={active === tab}" in js and "tabIndex={active === tab ? 0 : -1}" in js
    assert all(key in js for key in ("ArrowRight", "ArrowLeft", "Home", "End"))
    # Only one form shows at a time (the other panel is hidden, but stays mounted to keep its values).
    assert 'hidden={active !== "seniors"}' in js and 'hidden={active !== "partners"}' in js
    # Hero and marketplace buttons open the right tab; the marketplace ones pre-fill the form.
    assert js.count('openSignup("seniors"') == 2 and js.count('openSignup("partners"') == 2
    assert 'openSignup("partners", { type: "vendor" })' in js and 'openSignup("seniors", { sell: true })' in js
    # Smooth scrolling only when the visitor hasn't asked for reduced motion.
    assert "prefers-reduced-motion: reduce" in js
    # The event content comes before the sign-up section.
    assert js.index('className="wd-hero"') < js.index("wd-mission") < js.index("wd-basics") < js.index("wd-areas") < js.index("wd-offer") \
        < js.index("wd-services") < js.index("wd-market") < js.index("wd-community") < js.index("wd-about") \
        < js.index("<SignupTabs")


def test_page_lists_every_activity_and_type_the_api_accepts():
    from api.models import WELLNESS_ACTIVITIES, WELLNESS_PARTICIPATION, WELLNESS_VENDOR_CATEGORIES
    js = PAGE.read_text()

    def js_list(name):
        return re.findall(r'"([a-z_]+)"', js.split(f"const {name} = [", 1)[1].split("];", 1)[0])
    assert js_list("ACTIVITIES") == list(WELLNESS_ACTIVITIES)
    assert js_list("PARTICIPATION") == list(WELLNESS_PARTICIPATION)
    assert js_list("VENDOR_CATEGORIES") == list(WELLNESS_VENDOR_CATEGORIES)
    import json
    en = json.loads((ROOT / "src/front/locales/en.json").read_text())["wellnessDay"]
    assert set(en["interest"]["activityLabels"]) == set(WELLNESS_ACTIVITIES)
    cards = re.findall(r'key: "([a-z_]+)", slot:', js)
    assert set(cards) == set(en["offerings"]) and len(en["areas"]) == 7
    assert set(en["partner"]["vendorCategories"]) == set(WELLNESS_VENDOR_CATEGORIES) and "sea_moss" in WELLNESS_VENDOR_CATEGORIES
    assert set(en["partner"]["typeOptions"]) == set(WELLNESS_PARTICIPATION) == set(en["types"])
    assert en["partner"]["licenseNote"] == ("Massage and acupuncture must be provided by Massachusetts-licensed "
                                           "practitioners.")


def test_wellness_day_photo_slots():
    import json

    from api.commands import SITE_IMAGE_SLOTS
    from api.models import STOCK_ALLOWED_SLOTS, WELLNESS_DAY_STOCK_SLOTS
    js = PAGE.read_text()
    used = set(re.findall(r'"((?:wellness-day|seniors|research)-[a-z-]+)"', js))
    credits = json.loads((ROOT / "src/front/img/site/credits.json").read_text())
    assert set(WELLNESS_DAY_STOCK_SLOTS) <= set(STOCK_ALLOWED_SLOTS) and set(WELLNESS_DAY_STOCK_SLOTS) <= set(SITE_IMAGE_SLOTS)
    for slot in used:
        assert slot in SITE_IMAGE_SLOTS, slot
    # Our own photos where we have them.
    for ours in ("seniors-banner", "seniors-join", "research-banner", "seniors-baguazhang", "seniors-chair-massage"):
        assert ours in used and credits[ours]["type"] == "founder-owned"
    # No photo appears twice on the page; fall prevention takes our own photo only (never stock).
    slots = re.findall(r'slot(?:=|: )"([a-z-]+)"', js)
    assert len(slots) == len(set(slots)), slots
    assert "wellness-day-balance" not in STOCK_ALLOWED_SLOTS
    # Photos in the repo stay under 200 KB.
    site = ROOT / "src/front/img/site"
    for slot in used:
        f = site / f"{slot}.jpg"
        if f.exists():
            assert f.stat().st_size < 200_000, slot
    # Each stock photo is credited with its source page and license.
    for slot in WELLNESS_DAY_STOCK_SLOTS:
        if slot in credits:
            c = credits[slot]
            assert c["type"] == "stock" and c["page_url"].startswith(("https://unsplash.com/", "https://nappy.co/"))
            assert "license" in c["license"].lower()
