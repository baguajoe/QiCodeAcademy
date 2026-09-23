from datetime import timedelta

from api.models import (ContactMessage, GalleryPhoto, ImpactStat, NewsPost, Registration,
                        ResearchInterest, ResearchPartnerInquiry, ResearchReference, SiteImage,
                        SiteSetting, TeamMember, Volunteer, utcnow)

YOUTH = dict(type="youth", guardian_name="Pat Guardian", guardian_email="pat@example.org",
             guardian_phone="617-555-0100", participant_first_name="Sam",
             participant_last_name="Lee", grade="7", emergency_contact_name="Jo Lee",
             emergency_contact_phone="617-555-0101", photo_consent=False, guardian_consent=True)
SENIOR = dict(type="senior", participant_first_name="Mae", participant_last_name="Chan",
              email="mae@example.org", phone="617-555-0199", emergency_contact_name="Lin Chan",
              emergency_contact_phone="617-555-0198", photo_consent=True,
              comfort_notes="Prefer a chair near the door.")


# --- Programs ----------------------------------------------------------------
def test_programs_list_filters(client, make_program):
    make_program(title="Youth A", division="youth", neighborhood="Dorchester")
    make_program(title="Senior B", division="senior", neighborhood="Roxbury")
    make_program(title="Old C", division="youth", is_active=False)

    items = client.get("/api/programs").get_json()["items"]
    assert {p["title"] for p in items} == {"Youth A", "Senior B"}

    items = client.get("/api/programs?division=senior").get_json()["items"]
    assert [p["title"] for p in items] == ["Senior B"]

    items = client.get("/api/programs?neighborhood=dorchester").get_json()["items"]
    assert [p["title"] for p in items] == ["Youth A"]

    items = client.get("/api/programs?active=false").get_json()["items"]
    assert [p["title"] for p in items] == ["Old C"]

    assert len(client.get("/api/programs?active=all").get_json()["items"]) == 3
    assert client.get("/api/programs?division=nope").status_code == 400


def test_program_detail_seats_left(client, make_program):
    p = make_program(title="Tiny Class", capacity=2)
    res = client.get(f"/api/programs/{p.slug}")
    assert res.status_code == 200
    body = res.get_json()
    assert body["slug"] == "tiny-class"
    assert body["seats_left"] == 2 and body["is_full"] is False
    assert client.get("/api/programs/missing").status_code == 404


def test_slugs_are_unique(make_program):
    a = make_program(title="Same Name")
    b = make_program(title="Same Name")
    assert a.slug == "same-name" and b.slug == "same-name-2"


# --- Events ------------------------------------------------------------------
def test_events_upcoming_past_and_unpublished(client, make_event):
    make_event(title="Future", days=5, division="youth")
    make_event(title="Past", days=-5)
    make_event(title="Hidden", days=3, is_published=False)

    body = client.get("/api/events").get_json()
    assert [e["title"] for e in body["items"]] == ["Future"]
    assert body["total"] == 1 and body["page"] == 1
    assert body["items"][0]["timezone"] == "America/New_York"

    past = client.get("/api/events?when=past").get_json()["items"]
    assert [e["title"] for e in past] == ["Past"]
    assert client.get("/api/events?when=all").get_json()["total"] == 2
    assert client.get("/api/events?division=senior").get_json()["total"] == 0
    assert client.get("/api/events/hidden").status_code == 404


def test_event_ics(client, make_event):
    ev = make_event(title="Qigong, in the Park", location="Franklin Park")
    res = client.get(f"/api/events/{ev.slug}/ics")
    assert res.status_code == 200
    assert res.mimetype == "text/calendar"
    assert "attachment" in res.headers["Content-Disposition"]
    text = res.get_data(as_text=True)
    assert "BEGIN:VCALENDAR" in text and "BEGIN:VEVENT" in text
    assert "SUMMARY:Qigong\\, in the Park" in text
    assert "DTSTART;TZID=America/New_York:" in text


# --- Registrations -----------------------------------------------------------
def test_youth_registration_ok(client, db, make_program):
    p = make_program()
    res = client.post("/api/registrations", json={**YOUTH, "program_id": p.id})
    assert res.status_code == 201, res.get_json()
    assert res.get_json()["status"] == "pending"
    reg = db.session.query(Registration).one()
    assert reg.guardian_email == "pat@example.org"
    assert reg.email is None and reg.phone is None


def test_youth_registration_rejects_participant_contact(client, db, make_program):
    p = make_program()
    res = client.post("/api/registrations",
                      json={**YOUTH, "program_id": p.id, "email": "kid@example.org"})
    assert res.status_code == 400
    assert "email" in res.get_json()["errors"]
    assert db.session.query(Registration).count() == 0


def test_youth_registration_requires_guardian_and_consent(client, make_program):
    p = make_program()
    data = {**YOUTH, "program_id": p.id, "guardian_consent": False}
    del data["guardian_email"]
    errors = client.post("/api/registrations", json=data).get_json()["errors"]
    assert "guardian_email" in errors and "guardian_consent" in errors


def test_youth_email_never_stored_even_via_model(db, make_program):
    p = make_program()
    reg = Registration(**{**YOUTH, "program_id": p.id}, email="kid@x.org", phone="555-555-5555")
    db.session.add(reg)
    db.session.commit()
    assert reg.email is None and reg.phone is None


def test_senior_registration(client, db, make_program):
    p = make_program(division="senior")
    res = client.post("/api/registrations",
                      json={**SENIOR, "program_id": p.id, "guardian_name": "ignored"})
    assert res.status_code == 201, res.get_json()
    reg = db.session.query(Registration).one()
    assert reg.email == "mae@example.org" and reg.guardian_name is None
    assert reg.comfort_notes.startswith("Prefer")


def test_senior_requires_email_or_phone(client, make_program):
    p = make_program(division="senior")
    data = {**SENIOR, "program_id": p.id}
    del data["email"], data["phone"]
    assert client.post("/api/registrations", json=data).status_code == 400


def test_registration_type_must_match_division(client, make_program):
    p = make_program(division="senior")
    res = client.post("/api/registrations", json={**YOUTH, "program_id": p.id})
    assert res.status_code == 400 and "type" in res.get_json()["errors"]
    inter = make_program(division="intergenerational", title="Tech & Tea")
    assert client.post("/api/registrations", json={**YOUTH, "program_id": inter.id}).status_code == 201


def test_registration_inactive_program(client, make_program):
    p = make_program(is_active=False)
    assert client.post("/api/registrations", json={**YOUTH, "program_id": p.id}).status_code == 400


def test_waitlist_when_full(client, make_program):
    p = make_program(capacity=1)
    first = client.post("/api/registrations", json={**YOUTH, "program_id": p.id}).get_json()
    second = client.post("/api/registrations", json={**YOUTH, "program_id": p.id}).get_json()
    assert first["status"] == "pending"
    assert second["status"] == "waitlist" and second["waitlisted"] is True
    assert client.get(f"/api/programs/{p.slug}").get_json()["seats_left"] == 0


def test_honeypot_discards(client, db, make_program):
    p = make_program()
    res = client.post("/api/registrations", json={**YOUTH, "program_id": p.id,
                                                  "website": "http://spam.example"})
    assert res.status_code == 201 and res.get_json()["ok"] is True
    assert db.session.query(Registration).count() == 0
    for url in ("/api/volunteers", "/api/contact", "/api/research/inquiries",
                "/api/research/interest"):
        assert client.post(url, json={"website": "x"}).status_code == 201
    assert db.session.query(Volunteer).count() == 0
    assert db.session.query(ContactMessage).count() == 0


# --- Other forms -------------------------------------------------------------
def test_volunteer(client, db):
    res = client.post("/api/volunteers", json={
        "name": "Ava", "email": "ava@example.org",
        "roles": ["coding_mentor", "senior_tech_tutor", "coding_mentor"],
        "availability": "Weekends"})
    assert res.status_code == 201, res.get_json()
    assert db.session.query(Volunteer).one().roles == ["coding_mentor", "senior_tech_tutor"]
    bad = client.post("/api/volunteers", json={"name": "A", "email": "nope", "roles": ["chef"]})
    assert bad.status_code == 400
    assert {"email", "roles"} <= set(bad.get_json()["errors"])


def test_contact_types(client, db):
    assert client.post("/api/contact", json={"name": "B", "email": "b@example.org",
                                             "message": "Hi"}).status_code == 201
    assert client.post("/api/contact", json={"name": "C", "email": "c@example.org",
                                             "message": "I'd like to teach",
                                             "type": "guest_instructor"}).status_code == 201
    assert client.post("/api/contact", json={"name": "C", "email": "c@example.org",
                                             "message": "x", "type": "spam"}).status_code == 400
    assert {m.type for m in db.session.query(ContactMessage)} == {"general", "guest_instructor"}


def test_research_forms(client, db):
    assert client.post("/api/research/inquiries", json={
        "name": "Dr. R", "institution": "Some University", "email": "r@uni.edu",
        "area_of_interest": "Mind-body practice"}).status_code == 201
    assert db.session.query(ResearchPartnerInquiry).count() == 1

    assert client.post("/api/research/interest", json={
        "name": "Q", "email_or_phone": "617-555-0123", "consent_to_contact": True}).status_code == 201
    bad = client.post("/api/research/interest", json={
        "name": "Q", "email_or_phone": "not valid", "consent_to_contact": False})
    assert bad.status_code == 400
    assert {"email_or_phone", "consent_to_contact"} <= set(bad.get_json()["errors"])
    assert db.session.query(ResearchInterest).count() == 1


def test_research_interest_has_no_health_fields():
    cols = {c.name for c in ResearchInterest.__table__.columns}
    assert cols == {"id", "name", "email_or_phone", "neighborhood", "consent_to_contact",
                    "created_at", "updated_at"}


# --- Content -----------------------------------------------------------------
def test_news_published_only_and_paginated(client, db):
    db.session.add_all([
        NewsPost(title=f"Post {i}", body="<p>Hello <script>alert(1)</script>world</p>",
                 category="youth", is_published=True,
                 published_at=utcnow() - timedelta(days=i)) for i in range(1, 4)])
    db.session.add(NewsPost(title="Draft", body="x", is_published=False))
    db.session.add(NewsPost(title="Scheduled", body="x", is_published=True,
                            published_at=utcnow() + timedelta(days=3)))
    db.session.commit()

    body = client.get("/api/news?per_page=2").get_json()
    assert body["total"] == 3 and body["pages"] == 2 and len(body["items"]) == 2
    assert body["items"][0]["title"] == "Post 1"
    assert "body" not in body["items"][0] and body["items"][0]["excerpt"].startswith("Hello")
    assert client.get("/api/news?category=research").get_json()["total"] == 0

    detail = client.get("/api/news/post-1").get_json()
    assert "<script>" not in detail["body"]
    assert detail["published_at"].endswith("Z")
    assert client.get("/api/news/draft").status_code == 404
    assert client.get("/api/news/scheduled").status_code == 404


def test_team_partners_stats(client, db):
    db.session.add_all([TeamMember(name="B", group="staff", sort_order=2),
                        TeamMember(name="A", group="board", sort_order=1),
                        ImpactStat(label="Youth", value="40+")])
    db.session.commit()
    assert [t["name"] for t in client.get("/api/team").get_json()["items"]] == ["A", "B"]
    assert len(client.get("/api/team?group=board").get_json()["items"]) == 1
    assert client.get("/api/partners").get_json() == {"items": []}
    assert client.get("/api/impact-stats").get_json()["items"][0]["value"] == "40+"


def test_settings_public_only(client, db):
    db.session.add_all([SiteSetting(key="tax_status", value="Applied", is_public=True),
                        SiteSetting(key="internal_note", value="secret", is_public=False)])
    db.session.commit()
    assert client.get("/api/settings").get_json() == {"tax_status": "Applied"}


def test_site_images(client, db):
    db.session.add(SiteImage(slot_key="hero-home", image_url="/uploads/x.webp", alt_text="Kids coding"))
    db.session.add(SiteImage(slot_key="donate", image_url="", alt_text=""))
    db.session.commit()
    body = client.get("/api/site-images").get_json()
    assert body["hero-home"]["image_url"] == "/uploads/x.webp"
    assert body["donate"]["image_url"] is None


def test_gallery_published_only(client, db):
    db.session.add_all([
        GalleryPhoto(image_url="/a.webp", alt_text="A", division="youth",
                     consent_confirmed=True, is_published=True),
        GalleryPhoto(image_url="/b.webp", alt_text="B", division="senior",
                     consent_confirmed=True, is_published=False)])
    db.session.commit()
    body = client.get("/api/gallery").get_json()
    assert [p["alt_text"] for p in body["items"]] == ["A"]
    assert "consent_confirmed" not in body["items"][0]
    assert client.get("/api/gallery?division=senior").get_json()["total"] == 0


def test_gallery_cannot_publish_without_consent(db):
    import pytest
    from api.models import ModelRuleError
    db.session.add(GalleryPhoto(image_url="/c.webp", alt_text="C", is_published=True,
                                consent_confirmed=False))
    with pytest.raises(ModelRuleError):
        db.session.commit()
    db.session.rollback()


def test_research_references_verified_only(client, db):
    db.session.add_all([ResearchReference(title="Verified", year=2020, is_verified=True),
                        ResearchReference(title="Unverified", year=2021, is_verified=False)])
    db.session.commit()
    items = client.get("/api/research/references").get_json()["items"]
    assert [r["title"] for r in items] == ["Verified"]


def test_rate_limit_public_posts(rate_limited_app):
    client = rate_limited_app.test_client()
    payload = {"name": "B", "email": "b@example.org", "message": "Hi"}
    codes = [client.post("/api/contact", json=payload).status_code for _ in range(3)]
    assert codes == [201, 201, 429]
    assert client.post("/api/contact", json=payload).get_json()["error"] == "too_many_requests"
