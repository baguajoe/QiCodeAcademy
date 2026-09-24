import csv
import io

import pytest

from api.models import (ContactMessage, Donation, GalleryPhoto, Program, Registration,
                        ResearchInterest, ResearchPartnerInquiry, User, Volunteer)

from .conftest import ADMIN_EMAIL, ADMIN_PASSWORD
from .test_public import SENIOR, YOUTH


# --- Auth --------------------------------------------------------------------
def test_login_and_me(client, admin_user):
    res = client.post("/api/auth/login", json={"email": ADMIN_EMAIL.upper(), "password": ADMIN_PASSWORD})
    assert res.status_code == 200
    body = res.get_json()
    assert body["token_type"] == "Bearer" and body["user"]["email"] == ADMIN_EMAIL
    assert "password_hash" not in body["user"] and "password" not in body["user"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.get_json()["email"] == ADMIN_EMAIL


def test_login_failures(client, db, admin_user):
    assert client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "no@x.org", "password": "x"}).status_code == 401
    admin_user.is_active = False
    db.session.commit()
    assert client.post("/api/auth/login", json={"email": ADMIN_EMAIL,
                                                "password": ADMIN_PASSWORD}).status_code == 401


def test_admin_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/admin/programs").status_code == 401
    assert client.get("/api/admin/dashboard").status_code == 401
    assert client.get("/api/admin/programs", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get("/api/admin/registrations/export.csv").status_code == 401


def test_deactivated_admin_token_rejected(client, db, auth_headers, admin_user):
    admin_user.is_active = False
    db.session.commit()
    assert client.get("/api/admin/programs", headers=auth_headers).status_code == 401


def test_cors_preflight_not_blocked(client):
    res = client.options("/api/admin/programs", headers={
        "Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization"})
    assert res.status_code == 200
    assert res.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"


# --- CRUD --------------------------------------------------------------------
def test_program_crud(client, auth_headers):
    res = client.post("/api/admin/programs", headers=auth_headers, json={
        "division": "youth", "title": "Robotics", "capacity": 12, "cost": "Free",
        "start_date": "2026-10-01", "end_date": "2026-12-01", "website": "ignored"})
    assert res.status_code == 201, res.get_json()
    prog = res.get_json()
    assert prog["slug"] == "robotics" and prog["seats_left"] == 12

    res = client.patch(f"/api/admin/programs/{prog['id']}", headers=auth_headers,
                       json={"capacity": 5, "neighborhood": ""})
    assert res.status_code == 200
    assert res.get_json()["capacity"] == 5 and res.get_json()["neighborhood"] is None
    assert res.get_json()["title"] == "Robotics"

    bad = client.patch(f"/api/admin/programs/{prog['id']}", headers=auth_headers,
                       json={"end_date": "2026-01-01"})
    assert bad.status_code == 400 and "end_date" in bad.get_json()["errors"]

    listing = client.get("/api/admin/programs?q=robot", headers=auth_headers).get_json()
    assert listing["total"] == 1
    assert client.get(f"/api/admin/programs/{prog['id']}", headers=auth_headers).status_code == 200
    assert client.delete(f"/api/admin/programs/{prog['id']}", headers=auth_headers).status_code == 200
    assert client.get(f"/api/admin/programs/{prog['id']}", headers=auth_headers).status_code == 404


def test_duplicate_slug_conflict(client, auth_headers, make_program):
    make_program(title="Taken")
    res = client.post("/api/admin/programs", headers=auth_headers,
                      json={"division": "youth", "title": "Other", "slug": "taken"})
    assert res.status_code == 409


def test_program_with_registrations_cannot_be_deleted(client, db, auth_headers, make_program):
    p = make_program()
    db.session.add(Registration(**{**YOUTH, "program_id": p.id}))
    db.session.commit()
    assert client.delete(f"/api/admin/programs/{p.id}", headers=auth_headers).status_code == 409


def test_every_resource_lists(client, auth_headers):
    for name in ("users", "programs", "events", "registrations", "volunteers", "contact-messages",
                 "donations", "news", "team", "partners", "impact-stats", "settings",
                 "site-images", "gallery", "research-references", "research-inquiries",
                 "research-interest"):
        res = client.get(f"/api/admin/{name}", headers=auth_headers)
        assert res.status_code == 200, name
        assert "items" in res.get_json()


@pytest.mark.parametrize("name,payload,update", [
    ("events", {"division": "research", "title": "Talk", "start_datetime": "2026-11-01T18:00",
                "end_datetime": "2026-11-01T19:30"}, {"is_published": True}),
    ("volunteers", {"name": "V", "email": "v@x.org", "roles": ["event_help"]}, {"phone": "617-555-1111"}),
    ("contact-messages", {"name": "C", "email": "c@x.org", "message": "hi", "type": "partner"}, {"is_read": True}),
    ("donations", {"amount_cents": 5000, "designation": "youth", "status": "completed"}, {"donor_name": "Check donor"}),
    ("news", {"title": "Hello", "body": "<p>Hi</p><script>x</script>", "category": "youth"}, {"is_published": True}),
    ("team", {"name": "T", "group": "board", "role_title": "Chair"}, {"sort_order": 3}),
    ("partners", {"name": "P", "type": "sponsor", "website_url": "https://p.example"}, {"sort_order": 1}),
    ("impact-stats", {"label": "Learners", "value": "50"}, {"value": "60"}),
    ("settings", {"key": "contact_email", "value": "hi@x.org"}, {"is_public": False}),
    ("site-images", {"slot_key": "hero-home", "image_url": "/uploads/h.webp", "alt_text": "Hero"}, {"alt_text": "New"}),
    ("gallery", {"image_url": "/uploads/g.webp", "alt_text": "Group photo"}, {"caption": "Class"}),
    ("research-references", {"title": "A study", "year": 2019}, {"is_verified": True}),
    ("research-inquiries", {"name": "R", "institution": "U", "email": "r@u.edu"}, {"is_read": True}),
    ("research-interest", {"name": "N", "email_or_phone": "n@x.org", "consent_to_contact": True}, {"neighborhood": "Roxbury"}),
])
def test_generic_crud(client, auth_headers, name, payload, update):
    res = client.post(f"/api/admin/{name}", headers=auth_headers, json=payload)
    assert res.status_code == 201, (name, res.get_json())
    obj_id = res.get_json()["id"]
    res = client.put(f"/api/admin/{name}/{obj_id}", headers=auth_headers, json=update)
    assert res.status_code == 200, (name, res.get_json())
    for k, v in update.items():
        assert res.get_json()[k] == v
    assert client.delete(f"/api/admin/{name}/{obj_id}", headers=auth_headers).status_code == 200


def test_news_sanitized_and_published_at(client, auth_headers):
    res = client.post("/api/admin/news", headers=auth_headers, json={
        "title": "Hi", "body": '<p onclick="x()">Hi <a href="javascript:alert(1)">x</a></p><script>bad()</script>',
        "is_published": True})
    body = res.get_json()
    assert "<script>" not in body["body"] and "onclick" not in body["body"]
    assert "javascript:" not in body["body"]
    assert body["published_at"] is not None


def test_gallery_publish_requires_consent(client, db, auth_headers):
    res = client.post("/api/admin/gallery", headers=auth_headers, json={
        "image_url": "/uploads/g.webp", "alt_text": "Kids", "is_published": True})
    assert res.status_code == 400 and "is_published" in res.get_json()["errors"]
    res = client.post("/api/admin/gallery", headers=auth_headers, json={
        "image_url": "/uploads/g.webp", "alt_text": "Kids"})
    gid = res.get_json()["id"]
    assert client.patch(f"/api/admin/gallery/{gid}", headers=auth_headers,
                        json={"is_published": True}).status_code == 400
    ok = client.patch(f"/api/admin/gallery/{gid}", headers=auth_headers,
                      json={"is_published": True, "consent_confirmed": True})
    assert ok.status_code == 200 and ok.get_json()["is_published"] is True
    assert client.post("/api/admin/gallery", headers=auth_headers,
                       json={"image_url": "/uploads/g.webp"}).status_code == 400  # alt_text required


def test_registration_admin_rules(client, db, auth_headers, make_program):
    p = make_program()
    res = client.post("/api/admin/registrations", headers=auth_headers,
                      json={**YOUTH, "program_id": p.id, "status": "confirmed"})
    assert res.status_code == 201, res.get_json()
    rid = res.get_json()["id"]
    assert res.get_json()["program_title"] == p.title
    bad = client.patch(f"/api/admin/registrations/{rid}", headers=auth_headers,
                       json={"email": "kid@x.org"})
    assert bad.status_code == 400
    ok = client.patch(f"/api/admin/registrations/{rid}", headers=auth_headers,
                      json={"status": "cancelled", "admin_notes": "Moved away"})
    assert ok.status_code == 200 and ok.get_json()["status"] == "cancelled"
    listing = client.get(f"/api/admin/registrations?program_id={p.id}&status=cancelled",
                         headers=auth_headers).get_json()
    assert listing["total"] == 1
    assert client.post("/api/admin/registrations", headers=auth_headers,
                       json={**YOUTH, "program_id": 9999}).status_code == 400


def test_user_crud_never_leaks_hash(client, db, auth_headers, admin_user):
    res = client.post("/api/admin/users", headers=auth_headers,
                      json={"email": "New@Example.org", "name": "New", "password": "long-enough-pw"})
    assert res.status_code == 201, res.get_json()
    body = res.get_json()
    assert body["email"] == "new@example.org"
    assert "password" not in body and "password_hash" not in body
    assert client.post("/api/admin/users", headers=auth_headers,
                       json={"email": "x@example.org"}).status_code == 400  # password required
    assert client.post("/api/admin/users", headers=auth_headers,
                       json={"email": "new@example.org", "password": "long-enough-pw"}).status_code == 409
    listing = client.get("/api/admin/users", headers=auth_headers).get_data(as_text=True)
    assert "password" not in listing and "pbkdf2" not in listing and "scrypt" not in listing
    # password change works
    client.patch(f"/api/admin/users/{body['id']}", headers=auth_headers, json={"password": "another-long-pw"})
    assert client.post("/api/auth/login", json={"email": "new@example.org",
                                                "password": "another-long-pw"}).status_code == 200
    # can't delete or deactivate self
    assert client.delete(f"/api/admin/users/{admin_user.id}", headers=auth_headers).status_code == 400
    assert client.patch(f"/api/admin/users/{admin_user.id}", headers=auth_headers,
                        json={"is_active": False}).status_code == 400


def test_admin_list_filters_sort_paging(client, db, auth_headers):
    db.session.add_all([ContactMessage(name=f"N{i}", email="a@x.org", message="m",
                                       is_read=i % 2 == 0) for i in range(5)])
    db.session.commit()
    body = client.get("/api/admin/contact-messages?is_read=false&per_page=1&sort=name",
                      headers=auth_headers).get_json()
    assert body["total"] == 2 and body["pages"] == 2 and body["items"][0]["name"] == "N1"
    assert client.get("/api/admin/contact-messages?sort=nope", headers=auth_headers).status_code == 400


# --- CSV exports -------------------------------------------------------------
def _csv(res):
    return list(csv.reader(io.StringIO(res.get_data(as_text=True).lstrip("﻿"))))


def test_csv_exports(client, db, auth_headers, make_program):
    p = make_program()
    s = make_program(division="senior", title="Qigong")
    db.session.add_all([
        Registration(**{**YOUTH, "program_id": p.id, "participant_first_name": "=HYPERLINK(1)"}),
        Registration(**{**SENIOR, "program_id": s.id}),
        Volunteer(name="V", email="v@x.org", roles=["coding_mentor", "event_help"]),
        ResearchInterest(name="R", email_or_phone="r@x.org", consent_to_contact=True),
    ])
    db.session.commit()

    res = client.get("/api/admin/registrations/export.csv", headers=auth_headers)
    assert res.status_code == 200 and res.mimetype == "text/csv"
    rows = _csv(res)
    assert rows[0][0] == "id" and len(rows) == 3
    youth_row = next(r for r in rows[1:] if r[5] == "youth")
    assert youth_row[6] == "'=HYPERLINK(1)"  # formula injection neutralized
    assert youth_row[rows[0].index("email")] == ""

    only = _csv(client.get(f"/api/admin/registrations/export.csv?program_id={s.id}", headers=auth_headers))
    assert len(only) == 2

    vol = _csv(client.get("/api/admin/volunteers/export.csv", headers=auth_headers))
    assert vol[1][5] == "coding_mentor; event_help"
    ri = _csv(client.get("/api/admin/research-interest/export.csv", headers=auth_headers))
    assert ri[1][2] == "R" and ri[1][5] == "yes"


# --- Dashboard ---------------------------------------------------------------
def test_dashboard(client, db, auth_headers, make_program):
    p = make_program(capacity=3)
    db.session.add_all([
        Registration(**{**YOUTH, "program_id": p.id}, status="pending"),
        Registration(**{**YOUTH, "program_id": p.id}, status="confirmed"),
        Registration(**{**YOUTH, "program_id": p.id}, status="waitlist"),
        Donation(amount_cents=2500, designation="youth", status="completed"),
        Donation(amount_cents=1000, designation="youth", status="completed"),
        Donation(amount_cents=9999, designation="senior", status="pending"),
        ContactMessage(name="a", email="a@x.org", message="m"),
        ContactMessage(name="b", email="b@x.org", message="m", is_read=True),
        ResearchPartnerInquiry(name="r", institution="u", email="r@u.edu"),
    ])
    db.session.commit()
    d = client.get("/api/admin/dashboard", headers=auth_headers).get_json()
    row = d["registrations_by_program"][0]
    assert (row["pending"], row["confirmed"], row["waitlist"], row["seats_left"]) == (1, 1, 1, 1)
    assert d["donations"]["totals_by_designation"]["youth"] == {"amount_cents": 3500, "count": 2}
    assert d["donations"]["totals_by_designation"]["senior"]["amount_cents"] == 0
    assert d["donations"]["total_amount_cents"] == 3500
    assert len(d["donations"]["recent"]) == 2
    assert d["unread_messages"] == 1
    assert d["new_research_inquiries"] == 1


def test_image_alt_required(client, auth_headers):
    res = client.post("/api/admin/programs", headers=auth_headers, json={
        "division": "youth", "title": "Pics", "image_url": "/uploads/x.webp"})
    assert res.status_code == 400 and "image_alt" in res.get_json()["errors"]
    res = client.post("/api/admin/programs", headers=auth_headers, json={
        "division": "youth", "title": "Pics", "image_url": "/uploads/x.webp", "image_alt": "Kids coding"})
    assert res.status_code == 201
    res = client.post("/api/admin/news", headers=auth_headers, json={"title": "N", "cover_image_url": "/u.webp"})
    assert "cover_image_alt" in res.get_json()["errors"]
    res = client.post("/api/admin/events", headers=auth_headers, json={
        "division": "youth", "title": "E", "start_datetime": "2030-01-01T10:00", "image_url": "/u.webp"})
    assert "image_alt" in res.get_json()["errors"]


def test_registrations_photo_consent_filter(client, db, auth_headers, make_program):
    p = make_program()
    db.session.add_all([Registration(**{**YOUTH, "program_id": p.id, "photo_consent": True}),
                        Registration(**{**YOUTH, "program_id": p.id, "photo_consent": False})])
    db.session.commit()
    body = client.get("/api/admin/registrations?photo_consent=true", headers=auth_headers).get_json()
    assert body["total"] == 1 and body["items"][0]["photo_consent"] is True
