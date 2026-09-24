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
