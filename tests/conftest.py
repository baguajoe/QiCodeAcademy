import os
from datetime import date, datetime, timedelta

os.environ["APP_ENV"] = "testing"

import pytest  # noqa: E402

from api import create_app  # noqa: E402
from api.config import TestingConfig  # noqa: E402
from api.extensions import db as _db  # noqa: E402
from api.extensions import limiter  # noqa: E402
from api.models import Event, Program, User  # noqa: E402


@pytest.fixture
def app(tmp_path):
    app = create_app(TestingConfig, UPLOAD_FOLDER=str(tmp_path / "uploads"),
                     FRONTEND_DIST_DIR=str(tmp_path / "dist"))
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def make_program(db):
    def _make(**kw):
        defaults = dict(division="youth", title="Intro to Python", description="Learn Python",
                        neighborhood="Dorchester", capacity=10, is_active=True,
                        start_date=date.today() + timedelta(days=7))
        defaults.update(kw)
        p = Program(**defaults)
        db.session.add(p)
        db.session.commit()
        return p
    return _make


@pytest.fixture
def make_event(db):
    def _make(days=7, **kw):
        start = datetime.now().replace(microsecond=0, second=0) + timedelta(days=days)
        defaults = dict(division="community", title="Open House", description="Come by",
                        neighborhood="Roxbury", start_datetime=start,
                        end_datetime=start + timedelta(hours=2), is_published=True)
        defaults.update(kw)
        e = Event(**defaults)
        db.session.add(e)
        db.session.commit()
        return e
    return _make


ADMIN_EMAIL = "admin@example.org"
ADMIN_PASSWORD = "correct-horse-battery"


@pytest.fixture
def admin_user(db):
    u = User(email=ADMIN_EMAIL, name="Admin", is_active=True)
    u.set_password(ADMIN_PASSWORD)
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth_headers(client, admin_user):
    res = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['access_token']}"}


@pytest.fixture
def outbox(monkeypatch):
    """Capture outgoing emails instead of sending/printing them."""
    sent = []
    from api.services import email as email_service
    monkeypatch.setattr(email_service, "_deliver", lambda msg: sent.append(msg) or True)
    return sent


@pytest.fixture
def rate_limited_app(tmp_path):
    app = create_app(TestingConfig, RATELIMIT_ENABLED=True, RATELIMIT_FORMS="2 per minute",
                     UPLOAD_FOLDER=str(tmp_path / "uploads"))
    with app.app_context():
        _db.create_all()
        limiter.reset()
        yield app
        limiter.reset()
        _db.session.remove()
        _db.drop_all()
