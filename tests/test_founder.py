import hashlib
import json
import re
from pathlib import Path

from api.commands import (DEFAULT_SETTINGS, SITE_IMAGE_SLOTS, seed_founder, seed_settings,
                          upgrade_founder_text)
from api.founder_content import (FOUNDER_CREDENTIALS, FOUNDER_FULL_BIO, FOUNDER_NAME, FOUNDER_ROLE,
                                 FOUNDER_SHORT_BIO, LEGACY_FINGERPRINTS)
from api.models import SiteImage, SiteSetting, TeamMember

ROOT = Path(__file__).resolve().parents[1]

# The organization's final text, checked verbatim.
EXPECTED_SHORT_FIRST = (
    "Joseph Gallop brings 26 years of training and 18 years of professional teaching in the internal martial arts: "
    "Tai Chi, Baguazhang, and Xing Yi. A Boston native, he currently teaches at Grove Hall Senior Center, Codman "
    "Square Library, and in Boston City Parks, where he has taught since 2014.")
EXPECTED_BAGUA = ("Joseph's Baguazhang is in the Fu Style lineage of Fu Zhen Song, through Sun Baogang and Master Tak "
                  "Wong. He also studied Cao-style Yin Baguazhang under Chen Xiao Ping, and has taught a Baguazhang "
                  "workshop in Prague.")
EXPECTED_CREDENTIALS = [
    "Certified Tai Chi Instructor — training under Master Vincent Chu and Master Tak Wong",
    "200-Hour Yoga Instructor Certification — 33 Degree Yoga, 2020",
    "Massage Therapy Diploma — New England School of Therapeutics, 2021",
    "Myofascial Therapy Certification",
    "Asian Bodywork Therapy Certification — Master Tak Wong, 2023",
    "Full-Stack Web Developer Certification — 4Geeks Academy, 2024",
    "BS, Bowling Green State University, 1996",
]


def test_seed_founder_and_settings(client, db):
    seed_settings()
    assert seed_founder() is True
    assert seed_founder() is False  # idempotent
    db.session.commit()
    joseph = db.session.query(TeamMember).one()
    assert (joseph.name, joseph.role_title, joseph.group) == (FOUNDER_NAME, FOUNDER_ROLE, "staff")
    assert joseph.bio == FOUNDER_SHORT_BIO

    settings = client.get("/api/settings").get_json()
    for key in ("founder_full_bio", "founder_credentials", "press_globe_url", "press_wcvb_url",
                "org_contact_email", "org_contact_phone", "tax_status", "research_status"):
        assert key in settings, key
    assert settings["founder_full_bio"] == FOUNDER_FULL_BIO
    assert settings["founder_credentials"].splitlines() == EXPECTED_CREDENTIALS
    assert {s.slot_key for s in db.session.query(SiteImage)} == set(SITE_IMAGE_SLOTS)

    # Seeding again never overwrites staff edits
    db.session.query(SiteSetting).filter_by(key="founder_full_bio").one().value = "Edited"
    db.session.commit()
    seed_settings()
    upgrade_founder_text()
    db.session.commit()
    assert client.get("/api/settings").get_json()["founder_full_bio"] == "Edited"


def test_upgrade_replaces_only_unedited_legacy_text(db, monkeypatch):
    seed_settings()
    seed_founder()
    db.session.commit()
    joseph = db.session.query(TeamMember).one()
    joseph.bio = "an old seeded bio"
    creds = db.session.query(SiteSetting).filter_by(key="founder_credentials").one()
    creds.value = "an old credentials list"
    db.session.commit()
    fp = lambda s: hashlib.sha256(s.encode()).hexdigest()  # noqa: E731
    monkeypatch.setitem(LEGACY_FINGERPRINTS, "short_bio", {fp("an old seeded bio")})
    assert upgrade_founder_text() == 1  # credentials were "edited" (unknown fingerprint) → kept
    assert joseph.bio == FOUNDER_SHORT_BIO and creds.value == "an old credentials list"


def test_founder_text_is_verbatim():
    assert FOUNDER_SHORT_BIO.startswith(EXPECTED_SHORT_FIRST)
    assert FOUNDER_SHORT_BIO.endswith("His work has been featured in The Boston Globe and on WCVB Channel 5's Chronicles.")
    assert FOUNDER_SHORT_BIO.count("\n\n") == 2
    assert EXPECTED_BAGUA in FOUNDER_FULL_BIO
    assert ("He holds a myofascial therapy certification, an Asian Bodywork Therapy certification from Master Tak "
            "Wong, and a 200-hour yoga teacher certification from 33 Degree Yoga.") in FOUNDER_FULL_BIO
    for phrase in ("Gin Soon Tai Chi", "Grandmaster Gin Soon Chu", "Grandmaster Yang Sau Chung", "Yang Cheng Fu",
                   "Arthur Goodridge", "T.T. Liang", "650 hours", "Richmond Dickson", "Eye Forge Studios",
                   "Iron Dragon", "Maya 3D"):
        assert phrase in FOUNDER_FULL_BIO
    headings = re.findall(r"^## (.+)$", FOUNDER_FULL_BIO, re.M)
    assert headings == ["Lineage and training", "Bodywork and wellness", "Technology, media, and creative work"]
    assert FOUNDER_CREDENTIALS.splitlines() == EXPECTED_CREDENTIALS


def test_frontend_fallback_matches_backend():
    js = (ROOT / "src/front/js/founderContent.js").read_text()
    values = dict(re.findall(r'export const (\w+) = (".*?");\n', js, re.S))
    assert json.loads(values["FOUNDER_SHORT_BIO"]) == FOUNDER_SHORT_BIO
    assert json.loads(values["FOUNDER_FULL_BIO"]) == FOUNDER_FULL_BIO
    assert json.loads(values["FOUNDER_CREDENTIALS"]) == FOUNDER_CREDENTIALS
    assert json.loads(values["FOUNDER_NAME"]) == FOUNDER_NAME


def test_person_jsonld_uses_full_short_bio(client, db, app, tmp_path):
    (tmp_path / "dist").mkdir(exist_ok=True)
    (tmp_path / "dist" / "index.html").write_text("<html><head><title>x</title></head><body></body></html>")
    seed_founder()
    db.session.commit()
    html = client.get("/about/founder").get_data(as_text=True)
    ld = [json.loads(m) for m in re.findall(r'<script type="application/ld\+json" data-seo="1">(.*?)</script>', html)]
    person = next(d for d in ld if d["@type"] == "Person")
    assert person["description"] == " ".join(FOUNDER_SHORT_BIO.split("\n\n"))


def test_frontend_slots_match_backend_seed():
    js = (ROOT / "src/front/js/siteImages.js").read_text()
    block = js.split("export const SLOTS = {", 1)[1].split("\n};", 1)[0]
    front = set(re.findall(r'^  "?([a-z-]+)"?: \{', block, re.M))
    assert front == set(SITE_IMAGE_SLOTS)


def test_default_settings_public():
    assert all(is_public for _, _, is_public in DEFAULT_SETTINGS)
