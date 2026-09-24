import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _reload_config(monkeypatch, **env):
    for k in ("DATABASE_URL", "SITE_URL", "RAILWAY_PUBLIC_DOMAIN"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import api.config as config
    return importlib.reload(config)


def test_postgres_scheme_is_normalized(monkeypatch):
    cfg = _reload_config(monkeypatch, DATABASE_URL="postgres://u:p@host:5432/railway")
    assert cfg.Config.SQLALCHEMY_DATABASE_URI == "postgresql://u:p@host:5432/railway"
    cfg = _reload_config(monkeypatch, DATABASE_URL="postgresql://u:p@host:5432/railway")
    assert cfg.Config.SQLALCHEMY_DATABASE_URI == "postgresql://u:p@host:5432/railway"


def test_site_url_falls_back_to_railway_domain(monkeypatch):
    cfg = _reload_config(monkeypatch, RAILWAY_PUBLIC_DOMAIN="qicode.up.railway.app")
    assert cfg.Config.SITE_URL == "https://qicode.up.railway.app"
    cfg = _reload_config(monkeypatch, RAILWAY_PUBLIC_DOMAIN="qicode.up.railway.app", SITE_URL="https://qicodeacademy.org/")
    assert cfg.Config.SITE_URL == "https://qicodeacademy.org"
    _reload_config(monkeypatch)  # restore defaults for other tests


def test_railway_files():
    rj = json.loads((ROOT / "railway.json").read_text())
    assert rj["build"]["builder"] == "NIXPACKS"
    assert rj["deploy"]["healthcheckPath"] == "/api/health"
    assert rj["deploy"]["preDeployCommand"] == ["bash scripts/railway-predeploy.sh"]
    pre = (ROOT / "scripts/railway-predeploy.sh").read_text()
    assert "flask db upgrade" in pre and "flask seed --no-samples" in pre and "with-samples" not in pre
    start = (ROOT / "scripts/railway-start.sh").read_text()
    procfile_web = (ROOT / "Procfile").read_text().split("web:", 1)[1].strip()
    assert "gunicorn --chdir src app:app" in start and '0.0.0.0:${PORT:-3001}' in start
    assert "--threads 4 --timeout 60" in start and "--threads 4 --timeout 60" in procfile_web
    toml = (ROOT / "nixpacks.toml").read_text()
    assert 'providers = ["python", "node"]' in toml and "npm run build" in toml
