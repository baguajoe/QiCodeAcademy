from api.models import CurriculumModule


def _mod(db, **kw):
    defaults = dict(division="youth", title="Level 1", sort_order=1, is_published=True, status="in_development")
    defaults.update(kw)
    m = CurriculumModule(**defaults)
    db.session.add(m)
    db.session.commit()
    return m


def test_public_curriculum_published_sorted_filtered(client, db):
    _mod(db, title="Level 2", sort_order=2)
    _mod(db, title="Level 1", sort_order=1, learning_goals=["Loops"], projects=["Pong — game loops"],
         launch_label="Launching 2027")
    _mod(db, title="Draft", sort_order=0, is_published=False)
    _mod(db, division="senior", title="Tai Chi", status="available")
    items = client.get("/api/curriculum?division=youth").get_json()["items"]
    assert [m["title"] for m in items] == ["Level 1", "Level 2"]
    assert items[0]["projects"] == ["Pong — game loops"] and items[0]["launch_label"] == "Launching 2027"
    assert "is_published" not in items[0]
    assert len(client.get("/api/curriculum").get_json()["items"]) == 3
    assert client.get("/api/curriculum?division=research").get_json()["items"] == []
    assert client.get("/api/curriculum?division=bogus").status_code == 400


def test_admin_curriculum_crud_with_line_lists(client, auth_headers):
    res = client.post("/api/admin/curriculum", headers=auth_headers, json={
        "division": "senior", "title": "Traditional Baguazhang", "status": "available",
        "learning_goals": "Standing and stepping\n\nCircle walking\n  Palm positions  ",
        "projects": ["Standing and stepping", "Circle walking"], "is_published": True})
    assert res.status_code == 201, res.get_json()
    body = res.get_json()
    assert body["learning_goals"] == ["Standing and stepping", "Circle walking", "Palm positions"]
    res = client.patch(f"/api/admin/curriculum/{body['id']}", headers=auth_headers, json={"launch_label": "New"})
    assert res.status_code == 200 and res.get_json()["projects"] == ["Standing and stepping", "Circle walking"]
    assert client.post("/api/admin/curriculum", headers=auth_headers,
                       json={"division": "space", "title": "x"}).status_code == 400
    assert client.post("/api/admin/curriculum", headers=auth_headers,
                       json={"division": "youth", "title": "x", "status": "maybe"}).status_code == 400
    assert client.get("/api/admin/curriculum?division=senior", headers=auth_headers).get_json()["total"] == 1
    assert client.delete(f"/api/admin/curriculum/{body['id']}", headers=auth_headers).status_code == 200


def test_seeded_youth_levels(client, db):
    from api.commands import seed_curriculum
    assert seed_curriculum() >= 4
    db.session.commit()
    assert seed_curriculum() == 0  # idempotent
    items = client.get("/api/curriculum?division=youth").get_json()["items"]
    assert [m["title"] for m in items] == [
        "Level 1 — Python & Game Development",
        "Level 2 — Web & Application Development",
        "Level 3 — Intelligent Applications",
        "Level 4 — Advanced Projects, Entrepreneurship & Career Preparation",
    ]
    l1 = items[0]
    assert (l1["status"], l1["launch_label"], l1["age_range"]) == ("in_development", "Launching 2027", "Ages 14–18")
    assert l1["format_notes"] == ["Free for families", "Up to 15 students", "No coding experience needed"]
    assert len(l1["projects"]) == 12 and l1["projects"][0].startswith("Guess the Number — ")
    assert l1["projects"][-1] == "Finish, Portfolio & Demo Day — debugging, version control, portfolios, presenting your work"
    for m in items[1:]:
        assert m["status"] == "in_development" and m["projects"] == [] and m["summary"].count(".") == 1


def test_no_old_youth_age_wording():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    en = json.loads((root / "src/front/locales/en.json").read_text())
    assert en["youth"]["lead"] == "For teens ages 14–18. Programs for younger students are planned for the future."
    import re
    # Retired wording (built from parts so this test file doesn't contain it literally).
    retired = re.compile("|".join([
        "Ch" + "eng Style", "Grove Hall Commun" + "ity Center", "5" + "th grade",
        "Sun Ba ?" + "Gang", "Sun Ba" + "o Gang", "Sun Ba" + "i Gang"]), re.I)
    paths = [p for p in root.rglob("*") if p.is_file() and p.suffix in (".py", ".js", ".json", ".md", ".html")
             and not any(part in p.parts for part in ("node_modules", ".venv", "dist_manual", ".git"))]
    for path in paths:
        assert not retired.search(path.read_text(errors="ignore")), path


def test_seeded_senior_modules(client, db):
    from api.commands import seed_curriculum
    seed_curriculum()
    db.session.commit()
    items = client.get("/api/curriculum?division=senior").get_json()["items"]
    assert [m["title"] for m in items] == ["Traditional Yang-Style Tai Chi", "Traditional Baguazhang",
                                           "Yoga & Gentle Stretching", "Chair-Based Movement", "Breathing & Meditation"]
    tai_chi, bagua = items[0], items[1]
    assert "removing the two Snake Creeps Down sections" in tai_chi["learning_goals"][-1]
    assert tai_chi["projects"] == ["Foundations", "Sections of the form", "The complete form", "Ongoing refinement"]
    assert bagua["adaptations"].startswith("Large circles, slow steps")
    assert all(m["summary"].count(".") <= 1 for m in items[2:])


def test_seeded_research_signature_program(client, db):
    from api.commands import seed_curriculum
    seed_curriculum()
    db.session.commit()
    items = client.get("/api/curriculum?division=research").get_json()["items"]
    assert len(items) == 1
    m = items[0]
    assert m["title"] == "Baguazhang for Healthy Aging"
    assert (m["status"], m["launch_label"], m["duration"]) == ("in_development", "In development", "12 weeks (planned)")
    assert m["summary"].startswith("Our signature program: traditional Baguazhang circle walking, adapted for older adults.")
    assert m["learning_goals"] == ["Standing and stepping", "Circle walking in large, slow circles", "Palm positions",
                                   "Controlled changes of direction", "Support and chair options as needed"]


def test_featured_program_settings_public_and_editable(client, db, auth_headers):
    import json
    from pathlib import Path
    from api.commands import FEATURED_PROGRAM_TEXT, FEATURED_PROGRAM_TITLE, seed_settings
    seed_settings()
    db.session.commit()
    s = client.get("/api/settings").get_json()
    assert s["featured_program_title"] == FEATURED_PROGRAM_TITLE == "Baguazhang for Healthy Aging"
    assert s["featured_program_text"] == FEATURED_PROGRAM_TEXT
    # The frontend fallback copy matches the seeded default.
    en = json.loads((Path(__file__).resolve().parents[1] / "src/front/locales/en.json").read_text())
    assert (en["home"]["featuredTitle"], en["home"]["featuredText"]) == (FEATURED_PROGRAM_TITLE, FEATURED_PROGRAM_TEXT)
    assert en["research"]["programTitle"] == "Baguazhang for Healthy Aging"
    admin_js = (Path(__file__).resolve().parents[1] / "src/front/js/admin/SettingsScreen.js").read_text()
    assert '"featured_program_title"' in admin_js and '"featured_program_text"' in admin_js
    rows = client.get("/api/admin/settings?q=featured_program_title", headers=auth_headers).get_json()["items"]
    res = client.patch(f"/api/admin/settings/{rows[0]['id']}", headers=auth_headers, json={"value": "Walking the Circle"})
    assert res.status_code == 200, res.get_json()
    assert client.get("/api/settings").get_json()["featured_program_title"] == "Walking the Circle"
