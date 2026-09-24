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


def test_no_research_references_or_gallery_seeded():
    src = (ROOT / "src/api/commands.py").read_text()
    assert "ResearchReference(" not in src and "GalleryPhoto(" not in src


def test_samples_are_labeled():
    from api.commands import SAMPLE_STATS, sample_events, sample_programs
    from datetime import date
    assert all(p["title"].startswith("[SAMPLE]") for p in sample_programs(date.today()))
    assert all(e["title"].startswith("[SAMPLE]") for e in sample_events(date.today()))
    assert all(label.startswith("[SAMPLE]") for label, _ in SAMPLE_STATS)
