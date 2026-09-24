"""Site-wide content rules (see the brief's health & research language rules).

Scans every piece of hard-coded public copy — locale files, page components, email
templates, seed data — for wording that would claim a health benefit, promise tax
deductibility, or cite research. Fails the build if any slips in.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY_FILES = [
    *ROOT.glob("src/front/locales/*.json"),
    *ROOT.glob("src/front/js/pages/*.js"),
    *ROOT.glob("src/front/js/component/*.js"),
    ROOT / "src/api/commands.py",
    ROOT / "src/api/services/notifications.py",
    ROOT / "src/api/seo.py",
]

# Claims we never make about Tai Chi, Baguazhang, yoga, or bodywork.
FORBIDDEN = [
    r"\bprevents?\s+(falls?|disease|injur)",
    r"\b(cures?|heals?)\b",
    r"\btreats?\s+(pain|arthritis|disease|conditions?|symptoms?|anxiety|depression)",
    r"\breduces?\s+(the\s+)?(risk|falls?|pain|stress|blood)",
    r"\bimproves?\s+(balance|mobility|health|memory|strength)",
    r"\b(clinically\s+)?proven\b",
    r"\bstudies\s+show\b",
    r"\bresearch\s+(shows|proves)\b",
    r"\btax[- ]deductible\b",
    r"\bfully\s+deductible\b",
]
# Lines explicitly stating what we DON'T claim are allowed.
ALLOWED_CONTEXT = re.compile(r"(do not|don't|never|not)\s+(make|claim|promise|say)", re.I)


def _strings(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        def walk(v):
            if isinstance(v, dict):
                for x in v.values():
                    yield from walk(x)
            elif isinstance(v, list):
                for x in v:
                    yield from walk(x)
            elif isinstance(v, str):
                yield v
        return list(walk(json.loads(text)))
    return text.splitlines()


def test_no_health_or_deductibility_claims():
    problems = []
    for path in COPY_FILES:
        for line in _strings(path):
            if ALLOWED_CONTEXT.search(line):
                continue
            for pattern in FORBIDDEN:
                if re.search(pattern, line, re.I):
                    problems.append(f"{path.relative_to(ROOT)}: {pattern!r} in {line.strip()[:120]!r}")
    assert not problems, "Health/tax claim language found:\n" + "\n".join(problems)


def test_wellness_disclaimer_present():
    en = json.loads((ROOT / "src/front/locales/en.json").read_text())
    assert en["common"]["wellnessDisclaimer"] == (
        "Participants should consult their healthcare provider before starting a new exercise program.")
    seniors = (ROOT / "src/front/js/pages/Programs.js").read_text()
    assert seniors.count("<WellnessDisclaimer") >= 2  # senior + intergenerational pages
    assert "wellnessDisclaimer" in (ROOT / "src/front/js/component/Footer.js").read_text()


def test_research_roadmap_is_future_tense_and_notify_note():
    en = json.loads((ROOT / "src/front/locales/en.json").read_text())
    assert all(step.startswith("We will ") for step in en["research"]["roadmap"])
    assert en["research"]["notifyNote"] == "Joining this list does not enroll you in any study."


def test_research_references_seeded_hidden_and_gallery_founder_only(client, db):
    from api.commands import GALLERY_SEED, seed_gallery, seed_research_references
    from api.models import ResearchReference
    credits = json.loads((ROOT / "src/front/img/site/credits.json").read_text())
    for g in GALLERY_SEED:  # gallery seeds must be our own photos, never stock
        slot = g["image_url"].rsplit("/", 1)[1].rsplit(".", 1)[0]
        assert credits[slot]["type"] == "founder-owned"
    assert seed_gallery() == len(GALLERY_SEED) and seed_gallery() == 0
    db.session.commit()
    items = client.get("/api/gallery").get_json()["items"]
    assert sorted(i["image_url"] for i in items) == sorted(g["image_url"] for g in GALLERY_SEED)
    assert seed_research_references() == 3
    assert seed_research_references() == 0
    db.session.commit()
    refs = db.session.query(ResearchReference).all()
    assert all(r.is_verified is False and not r.url for r in refs)
    assert client.get("/api/research/references").get_json()["items"] == []  # hidden until verified


def test_samples_are_labeled_and_no_stats_seeded():
    import api.commands as commands
    from datetime import date
    assert all(p["title"].startswith("[SAMPLE]") for p in commands.sample_programs(date.today()))
    assert all(e["title"].startswith("[SAMPLE]") for e in commands.sample_events(date.today()))
    assert not hasattr(commands, "SAMPLE_STATS")
    assert "ImpactStat(" not in (ROOT / "src/api/commands.py").read_text()


def test_seed_adds_no_fake_content(app, db):
    from api.models import Event, ImpactStat, Program
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seed"])
    assert result.exit_code == 0, result.output
    assert db.session.query(ImpactStat).count() == 0
    assert db.session.query(Program).count() == 0 and db.session.query(Event).count() == 0
    runner.invoke(args=["seed", "--with-samples"])
    assert db.session.query(Program).count() > 0  # opt-in dev samples still work
    assert db.session.query(ImpactStat).count() == 0


def test_teaching_locations_names_only(client, db):
    from api.commands import seed_settings
    seed_settings()
    db.session.commit()
    locs = client.get("/api/settings").get_json()["teaching_locations"].splitlines()
    assert locs == ["Grove Hall Senior Center", "Parkway Community YMCA (West Roxbury)", "Codman Square Library",
                    "Boston City Parks"]
    # No street addresses (a number followed by a street word) anywhere in seeded settings or copy.
    street = re.compile(r"\b\d{1,5}\s+\w+(\s\w+)?\s+(St|Street|Ave|Avenue|Rd|Road|Blvd|Way|Sq|Square)\b", re.I)
    for path in COPY_FILES + [ROOT / "src/api/commands.py"]:
        assert not street.search(path.read_text()), path


def test_site_photo_credits_follow_photo_rules():
    from api.models import STOCK_ALLOWED_SLOTS
    site = ROOT / "src/front/img/site"
    credits = json.loads((site / "credits.json").read_text())
    files = {p.stem for p in site.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")}
    assert files == set(credits), "every photo file needs a credits.json entry (and vice versa)"
    stock_words = re.compile(r"\b(our|we|qi code|participants?|members?|students)\b", re.I)
    for slot, c in credits.items():
        assert c["type"] in ("stock", "founder-owned"), slot
        assert c["alt"] and c["license"] and c["credit"], slot
        if c["type"] == "stock":
            assert c["page_url"].startswith("https://"), f"stock photo needs its source page: {slot}"
        if c["type"] == "stock":
            assert slot in STOCK_ALLOWED_SLOTS, f"stock photo not allowed in {slot}"
            assert not stock_words.search(c["alt"]), f"stock alt text claims the people are ours: {slot}"
    for forbidden in ("founder-portrait", "founder-teaching"):
        assert credits.get(forbidden, {}).get("type") != "stock"


def test_no_loose_or_unblurred_photos_in_repo():
    """Original uploads must never be committed — only processed files in src/front/img/site/."""
    import subprocess
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    images = [f for f in tracked if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".heic"))]
    allowed = ("src/front/img/",)
    assert all(f.startswith(allowed) for f in images), [f for f in images if not f.startswith(allowed)]
    assert not [f for f in images if "youth" in f.lower() and "movement" not in f.lower() and "banner" not in f.lower()
                and "card" not in f.lower()]
    # Loose originals in the project root must be git-ignored so they can never be committed.
    loose = [f.name for f in ROOT.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic")]
    if loose:
        ignored = subprocess.run(["git", "check-ignore", *loose], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
        assert set(loose) == set(ignored), f"not git-ignored: {set(loose) - set(ignored)}"
