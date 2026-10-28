from datetime import datetime, timedelta

import pytest

from api.models import Event, NewsPost, SiteImage, TeamMember, utcnow

TEMPLATE = """<!doctype html><html><head>
<!--SEO-->
<title>Default</title>
<!--/SEO-->
</head><body><div id="app"></div></body></html>"""


@pytest.fixture
def dist(app, tmp_path):
    d = tmp_path / "dist"
    (d / "js").mkdir(parents=True)
    (d / "index.html").write_text(TEMPLATE)
    (d / "js" / "app.abc123.js").write_text("console.log(1)")
    app.config["FRONTEND_DIST_DIR"] = str(d)
    return d


def test_home_meta_and_org_jsonld(client, dist):
    res = client.get("/")
    html = res.get_data(as_text=True)
    assert res.status_code == 200
    assert "<title>Qi Code Academy — Learn. Move. Create. Connect.</title>" in html
    assert 'property="og:image" content="http://localhost:3001/img/social/default.jpg"' in html
    assert '"@type": "NGO"' in html and "NonprofitOrganization" in html
    assert "<title>Default</title>" not in html


def test_static_page_uses_its_social_image(client, db, dist):
    # Dedicated 1200x630 share images win over uploaded page photos (which aren't sized for previews).
    db.session.add(SiteImage(slot_key="youth-banner", image_url="https://cdn.example.org/y.webp", alt_text="Kids"))
    db.session.commit()
    html = client.get("/programs/youth").get_data(as_text=True)
    assert "<title>Youth Technology &amp; Workforce Development | Qi Code Academy</title>" in html
    assert 'og:image" content="http://localhost:3001/img/social/youth.jpg"' in html


SHARE_ROUTES = {
    "/": "default", "/about": "default", "/programs": "default", "/programs/youth": "youth",
    "/programs/seniors": "baguazhang", "/programs/seniors/wellness-day": "wellness-day",
    "/wellness-day": "wellness-day", "/programs/intergenerational": "default", "/research": "baguazhang",
    "/events": "default", "/get-involved": "default", "/contact": "default", "/donate": "default",
    "/gallery": "default", "/privacy": "default",
}


@pytest.mark.parametrize("path,image", SHARE_ROUTES.items())
def test_link_preview_tags_per_route(client, dist, path, image):
    html = client.get(path).get_data(as_text=True)
    img = f"http://localhost:3001/img/social/{image}.jpg"
    for tag in (f'property="og:image" content="{img}"', f'name="twitter:image" content="{img}"',
                'property="og:image:width" content="1200"', 'property="og:image:height" content="630"',
                'property="og:image:alt" content="', 'property="og:type" content="website"',
                'property="og:site_name" content="Qi Code Academy"', 'name="twitter:card" content="summary_large_image"',
                'property="og:title" content="', 'property="og:description" content="', 'name="twitter:title" content="',
                'name="twitter:description" content="'):
        assert tag in html, (path, tag)
    canonical = "/programs/seniors/wellness-day" if path == "/wellness-day" else path
    assert f'<link rel="canonical" href="http://localhost:3001{canonical}"' in html
    assert f'property="og:url" content="http://localhost:3001{canonical}"' in html


def test_share_descriptions_make_no_health_claims():
    from api.seo import STATIC_PAGES
    import re
    banned = re.compile(r"\b(improves?|prevents?|cures?|treats?|reduces?|heals?|boosts?|lowers?)\b", re.I)
    for path, (_, desc, _, _) in STATIC_PAGES.items():
        assert not banned.search(desc), (path, desc)


def test_social_images_and_favicons_exist_and_fit():
    from pathlib import Path
    from PIL import Image
    from api.seo import SOCIAL_IMAGES
    root = Path(__file__).resolve().parents[1] / "src/front/img"
    for name in SOCIAL_IMAGES:
        f = root / "social" / f"{name}.jpg"
        with Image.open(f) as im:
            assert im.format == "JPEG" and im.size == (1200, 630), name
        assert f.stat().st_size < 300 * 1024, name
    for icon, size in (("favicon-32x32.png", (32, 32)), ("apple-touch-icon.png", (180, 180))):
        with Image.open(root / "icons" / icon) as im:
            assert im.size == size
    with Image.open(root / "icons" / "favicon.ico") as im:
        assert im.format == "ICO"


def test_share_image_served_as_jpeg_not_spa(client, dist):
    (dist / "img" / "social").mkdir(parents=True)
    (dist / "img" / "social" / "default.jpg").write_bytes(b"\xff\xd8\xff\xe0fakejpeg")
    (dist / "favicon.ico").write_bytes(b"\x00\x00\x01\x00")
    res = client.get("/img/social/default.jpg")
    assert res.status_code == 200 and res.mimetype == "image/jpeg"
    ico = client.get("/favicon.ico")
    assert ico.status_code == 200 and "icon" in ico.mimetype
    assert client.get("/img/social/missing.jpg").status_code == 404


def test_founder_person_jsonld(client, db, dist):
    db.session.add(TeamMember(name="Joseph Gallop", role_title="Founder & Principal Instructor", bio="Short bio.\n\nMore."))
    db.session.commit()
    html = client.get("/about/founder").get_data(as_text=True)
    assert '"@type": "Person"' in html and '"description": "Short bio. More."' in html


def test_event_page_jsonld_with_boston_offset(client, db, dist):
    db.session.add(Event(title="Qigong <Park>", slug="qigong", division="senior", is_published=True,
                         start_datetime=datetime(2030, 7, 1, 9, 30), end_datetime=datetime(2030, 7, 1, 10, 30)))
    db.session.commit()
    html = client.get("/events/qigong").get_data(as_text=True)
    assert '"@type": "Event"' in html
    assert '"startDate": "2030-07-01T09:30:00-04:00"' in html
    assert "<title>Qigong &lt;Park&gt; | Qi Code Academy</title>" in html  # escaped
    assert client.get("/events/nope").status_code == 404


def test_unknown_page_404_and_noindex(client, dist):
    res = client.get("/definitely-not-a-page")
    assert res.status_code == 404
    assert 'name="robots" content="noindex' in res.get_data(as_text=True)
    assert 'content="noindex' in client.get("/donate/thank-you").get_data(as_text=True)
    assert client.get("/admin/registrations").status_code == 200


def test_jsonld_cannot_break_out_of_script(client, db, dist):
    db.session.add(Event(title="x", slug="evil", division="community", is_published=True,
                         description="</script><script>alert(1)</script>", start_datetime=datetime(2030, 1, 1, 10)))
    db.session.commit()
    html = client.get("/events/evil").get_data(as_text=True)
    assert "</script><script>alert(1)" not in html


def test_works_with_minified_template(client, dist):
    (dist / "index.html").write_text('<!doctype html><html lang=en><head><meta charset=utf-8><title>Old</title>'
                                  '<meta name=description content="old" data-seo=1></head><body></body></html>')
    html = client.get("/about").get_data(as_text=True)
    assert html.count("<title>") == 1 and "<title>About | Qi Code Academy</title>" in html
    assert 'content="old"' not in html and html.count('name="description"') == 1


def test_hashed_assets_cached_long(client, dist):
    res = client.get("/js/app.abc123.js")
    assert "max-age=31536000" in res.headers["Cache-Control"]
    assert client.get("/about").headers["Cache-Control"] == "no-cache"


def test_sitemap_and_robots(client, db, dist):
    db.session.add(Event(title="E", slug="e1", division="youth", is_published=True, start_datetime=datetime(2030, 1, 1)))
    db.session.add(Event(title="Hidden", slug="hidden", division="youth", is_published=False, start_datetime=datetime(2030, 1, 1)))
    db.session.add(NewsPost(title="N", slug="n1", body="x", is_published=True, published_at=utcnow() - timedelta(days=1)))
    db.session.commit()
    xml = client.get("/sitemap.xml").get_data(as_text=True)
    assert "<loc>http://localhost:3001/events/e1</loc>" in xml and "hidden" not in xml
    assert "/news/n1" in xml and "/about/founder" in xml and "/donate/thank-you" not in xml
    robots = client.get("/robots.txt").get_data(as_text=True)
    assert "Disallow: /admin" in robots and "Sitemap: http://localhost:3001/sitemap.xml" in robots
