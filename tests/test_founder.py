import json
import re
from pathlib import Path

from api.commands import DEFAULT_SETTINGS, SITE_IMAGE_SLOTS, seed_founder, seed_settings
from api.founder_content import (FOUNDER_CREDENTIALS, FOUNDER_FULL_BIO, FOUNDER_NAME, FOUNDER_ROLE,
                                 FOUNDER_SHORT_BIO)
from api.models import SiteImage, SiteSetting, TeamMember

ROOT = Path(__file__).resolve().parents[1]


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
    assert settings["founder_credentials"].splitlines()[-1] == "BS, Bowling Green State University, 1996"
    assert {s.slot_key for s in db.session.query(SiteImage)} == set(SITE_IMAGE_SLOTS)

    # Seeding again never overwrites staff edits
    db.session.query(SiteSetting).filter_by(key="founder_full_bio").one().value = "Edited"
    db.session.commit()
    seed_settings()
    db.session.commit()
    assert client.get("/api/settings").get_json()["founder_full_bio"] == "Edited"


def test_founder_text_is_verbatim():
    # Spot-check exact phrases (lineage names, dates) from the organization's copy.
    for phrase in ("Grove Hall Community Center since 2016", "Boston City Parks since 2014",
                   "Master Vincent Chu", "Prague", "WCVB Channel 5's Chronicles"):
        assert phrase in FOUNDER_SHORT_BIO
    for phrase in ("Gin Soon Tai Chi", "Grandmaster Gin Soon Chu", "Grandmaster Yang Sau Chung",
                   "Yang Cheng Fu", "Arthur Goodridge", "T.T. Liang", "Fu Style lineage",
                   "Sun Ba Gang", "Fu Zhen Song", "Master Tak Wong", "Yin Style Baguazhang of the Cao family",
                   "Chen Xiao Ping", "650 hours", "Richmond Dickson", "33 Degree Yoga",
                   "Eye Forge Studios", "Iron Dragon", "Maya 3D"):
        assert phrase in FOUNDER_FULL_BIO
    headings = re.findall(r"^## (.+)$", FOUNDER_FULL_BIO, re.M)
    assert headings == ["Lineage and training", "Bodywork and wellness", "Technology, media, and creative work"]
    assert len(FOUNDER_CREDENTIALS.splitlines()) == 6


def test_frontend_fallback_matches_backend():
    js = (ROOT / "src/front/js/founderContent.js").read_text()
    values = dict(re.findall(r'export const (\w+) = (".*?");\n', js, re.S))
    assert json.loads(values["FOUNDER_SHORT_BIO"]) == FOUNDER_SHORT_BIO
    assert json.loads(values["FOUNDER_FULL_BIO"]) == FOUNDER_FULL_BIO
    assert json.loads(values["FOUNDER_CREDENTIALS"]) == FOUNDER_CREDENTIALS
    assert json.loads(values["FOUNDER_NAME"]) == FOUNDER_NAME


def test_frontend_slots_match_backend_seed():
    js = (ROOT / "src/front/js/siteImages.js").read_text()
    block = js.split("export const SLOTS = {", 1)[1].split("\n};", 1)[0]
    front = set(re.findall(r'^  "?([a-z-]+)"?: \{', block, re.M))
    assert front == set(SITE_IMAGE_SLOTS)


def test_default_settings_public():
    assert all(is_public for _, _, is_public in DEFAULT_SETTINGS)
