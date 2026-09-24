"""Server-side SEO for the React app.

Crawlers and link-preview bots (Facebook, iMessage, Slack…) don't run JavaScript,
so when Flask serves index.html it swaps in the page's
title, description, canonical URL, Open Graph/Twitter tags and JSON-LD. The React
app replaces these same tags (data-seo="1") as visitors navigate.

Also: /sitemap.xml and /robots.txt, and real 404 status codes for unknown pages.
Page titles/descriptions here mirror src/front/locales/en.json.
"""
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Response, current_app
from sqlalchemy import select

from .extensions import db
from .models import Event, NewsPost, Program, SiteImage, SiteSetting, TeamMember, utcnow
from .founder_content import FOUNDER_NAME, FOUNDER_ROLE, FOUNDER_SHORT_BIO

SITE = "Qi Code Academy"
TAGLINE = "Learn. Move. Create. Connect."
MISSION = ("Qi Code Academy empowers youth and older adults in Boston's inner-city communities through "
           "technology education, workforce development, wellness, community engagement, and research.")
NEIGHBORHOODS = ["Dorchester", "Roxbury", "Mattapan", "Hyde Park", "South End"]

# path -> (title or None for the home page, description, share-image slot, indexable)
STATIC_PAGES = {
    "/": (None, MISSION, "hero-home", True),
    "/about": ("About", MISSION, "about-banner", True),
    "/about/founder": (f"{FOUNDER_NAME}, {FOUNDER_ROLE}", FOUNDER_SHORT_BIO.split("\n\n")[0], "founder-portrait", True),
    "/programs/youth": ("Youth Technology & Workforce Development",
                        "Python, game development, AI, 3D animation, and career readiness for young people in "
                        "Boston's neighborhoods, starting around 5th grade.", "youth-banner", True),
    "/programs/seniors": ("Senior Wellness & Healthy Aging",
                          "Traditional Tai Chi, Baguazhang, yoga, wellness education, and social time for older "
                          "adults, designed to encourage healthy and active aging.", "seniors-banner", True),
    "/programs/intergenerational": ("Intergenerational Programs",
                                    "Youth help older adults learn technology: young people gain leadership "
                                    "experience, and seniors gain digital skills.", "intergenerational-banner", True),
    "/research": ("Research & Community Health",
                  "Building toward community-based research into traditional movement and mind-body practices, "
                  "especially Baguazhang.", "research-banner", True),
    "/events": ("Events", "Classes, open houses, workshops, and community gatherings.", "events-banner", True),
    "/news": ("News", "Updates from our programs and community.", None, True),
    "/gallery": ("Gallery", "Photos from our classes and events, shared with the permission of everyone pictured.", None, True),
    "/get-involved": ("Get Involved", "Volunteer, teach, partner, or sponsor — there are many ways to help.", "volunteer-banner", True),
    "/contact": ("Contact us", "Questions about programs, volunteering, or partnerships? Send us a note.", None, True),
    "/donate": ("Donate", "Support technology education for young people and wellness programs for older adults in Boston.", "donate", True),
    "/donate/thank-you": ("Thank you for your gift!", MISSION, None, False),
    "/donate/cancelled": ("Your donation was cancelled", MISSION, None, False),
    "/privacy": ("Privacy Policy", MISSION, None, False),
    "/terms": ("Terms of Use", MISSION, None, False),
    "/register": ("Register", "Choose a program to begin registration.", None, False),
    "/programs": (None, MISSION, "hero-home", False),  # redirects client-side
}
SITEMAP_PATHS = [p for p, v in STATIC_PAGES.items() if v[3]]
NOINDEX_PREFIXES = ("/register/", "/admin")

_template_cache = {}


def _site_url():
    return current_app.config["SITE_URL"].rstrip("/")


def _abs(url):
    if not url:
        return None
    return url if url.startswith("http") else _site_url() + url


def _settings():
    rows = db.session.scalars(select(SiteSetting).where(SiteSetting.is_public.is_(True)))
    return {r.key: r.value for r in rows}


def share_image(slot, dist):
    if slot:
        row = db.session.scalar(select(SiteImage).where(SiteImage.slot_key == slot))
        if row and row.image_url:
            return _abs(row.image_url)
        for ext in ("jpg", "jpeg", "png", "webp"):
            if (dist / "img" / "site" / f"{slot}.{ext}").is_file():
                return f"{_site_url()}/img/site/{slot}.{ext}"
    return f"{_site_url()}/img/og-default.png"


def org_jsonld(settings):
    data = {
        "@context": "https://schema.org",
        "@type": "NGO",
        "additionalType": "https://schema.org/NonprofitOrganization",
        "name": SITE,
        "legalName": "Qi Code Academy, Inc.",
        "url": _site_url(),
        "logo": f"{_site_url()}/img/og-default.png",
        "slogan": TAGLINE,
        "description": MISSION,
        "areaServed": [{"@type": "Place", "name": f"{n}, Boston, MA"} for n in NEIGHBORHOODS],
        "address": {"@type": "PostalAddress", "addressLocality": "Boston", "addressRegion": "MA", "addressCountry": "US"},
    }
    same_as = [settings.get(k) for k in ("social_facebook", "social_instagram", "social_youtube") if settings.get(k)]
    if same_as:
        data["sameAs"] = same_as
    if settings.get("org_contact_email"):
        data["email"] = settings["org_contact_email"]
    if settings.get("org_contact_phone"):
        data["telephone"] = settings["org_contact_phone"]
    return data


def _ny_iso(dt):
    return dt.replace(tzinfo=ZoneInfo("America/New_York")).isoformat() if dt else None


def event_jsonld(ev, url):
    place = ev.location or ev.neighborhood or "Boston"
    data = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": ev.title,
        "description": ev.description or "",
        "startDate": _ny_iso(ev.start_datetime),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {"@type": "Place", "name": place, "address": {
            "@type": "PostalAddress",
            "addressLocality": f"{ev.neighborhood}, Boston" if ev.neighborhood else "Boston",
            "addressRegion": "MA", "addressCountry": "US"}},
        "organizer": {"@type": "NGO", "name": SITE, "url": _site_url()},
        "url": url,
    }
    if ev.end_datetime:
        data["endDate"] = _ny_iso(ev.end_datetime)
    if ev.image_url:
        data["image"] = [_abs(ev.image_url)]
    return data


def person_jsonld():
    member = db.session.scalar(select(TeamMember).where(TeamMember.name == FOUNDER_NAME))
    bio = (member.bio if member and member.bio else FOUNDER_SHORT_BIO).split("\n\n")[0]
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": FOUNDER_NAME,
        "jobTitle": (member.role_title if member and member.role_title else FOUNDER_ROLE),
        "description": bio,
        "url": f"{_site_url()}/about/founder",
        "worksFor": {"@type": "NGO", "name": SITE, "legalName": "Qi Code Academy, Inc.", "url": _site_url()},
    }


def _clip(text, n=300):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def page_meta(path, dist):
    """Return (meta dict, http_status)."""
    path = path.rstrip("/") or "/"
    settings = _settings()
    meta = {"title": None, "description": MISSION, "image": None, "type": "website", "noindex": False,
            "jsonld": [org_jsonld(settings)]}
    status = 200

    if path in STATIC_PAGES:
        title, desc, slot, indexable = STATIC_PAGES[path]
        meta.update(title=title, description=_clip(desc), image=share_image(slot, dist), noindex=not indexable)
        if path == "/about/founder":
            meta["type"] = "profile"
            meta["jsonld"].append(person_jsonld())
    elif m := re.fullmatch(r"/events/([\w-]+)", path):
        ev = db.session.scalar(select(Event).where(Event.slug == m.group(1), Event.is_published.is_(True)))
        if ev:
            when = ev.start_datetime.strftime("%A, %B %-d, %Y, %-I:%M %p")
            meta.update(title=ev.title, description=_clip(f"{when}. {ev.description or ''}"),
                        image=_abs(ev.image_url) or share_image("events-banner", dist))
            meta["jsonld"].append(event_jsonld(ev, _site_url() + path))
        else:
            status = 404
    elif m := re.fullmatch(r"/news/([\w-]+)", path):
        post = db.session.scalar(select(NewsPost).where(NewsPost.slug == m.group(1), NewsPost.is_published.is_(True),
                                                        NewsPost.published_at <= utcnow()))
        if post:
            text = re.sub(r"<[^>]+>", " ", post.body or "")
            meta.update(title=post.title, description=_clip(text), type="article",
                        image=_abs(post.cover_image_url) or share_image(None, dist))
        else:
            status = 404
    elif m := re.fullmatch(r"/register/([\w-]+)", path):
        program = db.session.scalar(select(Program).where(Program.slug == m.group(1)))
        if program:
            meta.update(title=f"Register: {program.title}", noindex=True)
        else:
            status = 404
    elif path == "/admin" or path.startswith("/admin/"):
        meta.update(title="Admin", noindex=True)
    else:
        status = 404

    if status == 404:
        meta.update(title="Page not found", noindex=True)
    if not meta["image"]:
        meta["image"] = share_image(None, dist)
    return meta, status


def render_head(meta, path):
    full_title = f"{meta['title']} | {SITE}" if meta["title"] else f"{SITE} — {TAGLINE}"
    url = _site_url() + (path.rstrip("/") or "/")
    e = lambda v: escape(v or "", quote=True)  # noqa: E731
    tags = [
        f"<title>{e(full_title)}</title>",
        f'<meta name="description" content="{e(meta["description"])}" data-seo="1" />',
        f'<link rel="canonical" href="{e(url)}" data-seo="1" />',
        f'<meta property="og:site_name" content="{SITE}" data-seo="1" />',
        f'<meta property="og:type" content="{e(meta["type"])}" data-seo="1" />',
        f'<meta property="og:title" content="{e(full_title)}" data-seo="1" />',
        f'<meta property="og:description" content="{e(meta["description"])}" data-seo="1" />',
        f'<meta property="og:url" content="{e(url)}" data-seo="1" />',
        f'<meta property="og:image" content="{e(meta["image"])}" data-seo="1" />',
        '<meta property="og:locale" content="en_US" data-seo="1" />',
        '<meta name="twitter:card" content="summary_large_image" data-seo="1" />',
        f'<meta name="twitter:title" content="{e(full_title)}" data-seo="1" />',
        f'<meta name="twitter:description" content="{e(meta["description"])}" data-seo="1" />',
        f'<meta name="twitter:image" content="{e(meta["image"])}" data-seo="1" />',
    ]
    if meta["noindex"]:
        tags.append('<meta name="robots" content="noindex, nofollow" data-seo="1" />')
    for block in meta["jsonld"]:
        # Escape "</" so JSON can't close the script tag.
        payload = json.dumps(block, ensure_ascii=False).replace("</", "<\\/")
        tags.append(f'<script type="application/ld+json" data-seo="1">{payload}</script>')
    return "\n    ".join(tags)


def _template(dist: Path):
    index = dist / "index.html"
    mtime = index.stat().st_mtime
    cached = _template_cache.get(str(index))
    if not cached or cached[0] != mtime:
        cached = (mtime, index.read_text(encoding="utf-8"))
        _template_cache[str(index)] = cached
    return cached[1]


_TITLE_RE = re.compile(r"<title>.*?</title>", re.S | re.I)
# Default SEO tags from the template carry data-seo (quoted or, once minified, unquoted).
_DEFAULT_SEO_RE = re.compile(r"<(meta|link)\b[^>]*\bdata-seo(=\"?1\"?)?[^>]*>", re.I)
_MARKERS_RE = re.compile(r"<!--/?SEO-->")


def render_index(dist: Path, path: str):
    """index.html with this page's SEO tags. Works whether or not webpack minified the HTML."""
    meta, status = page_meta(path, dist)
    html = _TITLE_RE.sub("", _template(dist), count=1)
    html = _MARKERS_RE.sub("", _DEFAULT_SEO_RE.sub("", html))
    html = html.replace("</head>", f"{render_head(meta, path)}\n</head>", 1)
    resp = Response(html, status=status, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


def sitemap():
    base = _site_url()
    urls = [(base + (p if p != "/" else "/"), None) for p in SITEMAP_PATHS]
    for slug, updated in db.session.execute(select(Event.slug, Event.updated_at).where(Event.is_published.is_(True))):
        urls.append((f"{base}/events/{slug}", updated))
    for slug, updated in db.session.execute(
            select(NewsPost.slug, NewsPost.updated_at).where(NewsPost.is_published.is_(True), NewsPost.published_at <= utcnow())):
        urls.append((f"{base}/news/{slug}", updated))
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, updated in urls:
        lastmod = f"<lastmod>{updated.date().isoformat()}</lastmod>" if isinstance(updated, datetime) else ""
        body.append(f"  <url><loc>{escape(loc)}</loc>{lastmod}</url>")
    body.append("</urlset>")
    return Response("\n".join(body) + "\n", mimetype="application/xml")


def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin",
        "Disallow: /flask-admin",
        "Disallow: /api/",
        "Disallow: /register",
        "Disallow: /donate/thank-you",
        "Disallow: /donate/cancelled",
        "",
        f"Sitemap: {_site_url()}/sitemap.xml",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")
