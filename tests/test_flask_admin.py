import re

from api.models import GalleryPhoto, Program

from .conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def _login(client, password=ADMIN_PASSWORD):
    page = client.get("/flask-admin/login").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    return client.post("/flask-admin/login", data={"email": ADMIN_EMAIL, "password": password,
                                                   "csrf_token": token})


def _form_csrf(client, url):
    page = client.get(url).get_data(as_text=True)
    return re.search(r'id="csrf_token" name="csrf_token" type="hidden" value="([^"]+)"', page).group(1)


def test_flask_admin_requires_login(client, admin_user):
    res = client.get("/flask-admin/")
    assert res.status_code == 302 and "/flask-admin/login" in res.headers["Location"]
    res = client.get("/flask-admin/fa_programs/")
    assert res.status_code == 302 and "/flask-admin/login" in res.headers["Location"]


def test_flask_admin_login_logout(client, admin_user):
    assert _login(client, "wrong-password").status_code == 200  # re-renders with error
    assert client.get("/flask-admin/").status_code == 302
    res = _login(client)
    assert res.status_code == 302
    home = client.get("/flask-admin/")
    assert home.status_code == 200 and "Pending registrations" in home.get_data(as_text=True)
    assert client.get("/flask-admin/fa_registrations/").status_code == 200
    users_page = client.get("/flask-admin/fa_users/").get_data(as_text=True)
    assert ADMIN_EMAIL in users_page and "password_hash" not in users_page
    client.get("/flask-admin/logout")
    assert client.get("/flask-admin/").status_code == 302


def test_login_rejects_missing_csrf(client, admin_user):
    client.get("/flask-admin/login")
    client.post("/flask-admin/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert client.get("/flask-admin/").status_code == 302


def test_every_view_renders(client, admin_user):
    _login(client)
    for ep in ("fa_registrations", "fa_volunteers", "fa_contact_messages", "fa_donations",
               "fa_programs", "fa_events", "fa_news_posts", "fa_gallery_photos", "fa_team_members",
               "fa_partners", "fa_impact_stats", "fa_site_images", "fa_site_settings",
               "fa_research_references", "fa_research_partner_inquiries", "fa_research_interest",
               "fa_users"):
        assert client.get(f"/flask-admin/{ep}/").status_code == 200, ep
        assert client.get(f"/flask-admin/{ep}/new/").status_code == 200, ep


def test_create_program_via_flask_admin_autoslugs(client, db, admin_user):
    _login(client)
    token = _form_csrf(client, "/flask-admin/fa_programs/new/")
    res = client.post("/flask-admin/fa_programs/new/", data={
        "csrf_token": token, "division": "youth", "title": "Panel Program", "description": "d",
        "is_active": "y"})
    assert res.status_code == 302
    assert db.session.query(Program).one().slug == "panel-program"


def test_gallery_consent_enforced_in_flask_admin(client, db, admin_user):
    _login(client)
    token = _form_csrf(client, "/flask-admin/fa_gallery_photos/new/")
    client.post("/flask-admin/fa_gallery_photos/new/", data={
        "csrf_token": token, "image_url": "/uploads/x.webp", "alt_text": "Alt", "division": "youth",
        "is_published": "y", "sort_order": "0"})
    assert db.session.query(GalleryPhoto).count() == 0
