"""501(c)(3) approval: settings, seed upgrade of live values, footer/JSON-LD data, the IRS letter."""
import json
import re
from pathlib import Path

from api.commands import (DEFAULT_SETTINGS, DONATIONS_NOTICE, EIN, ORG_HISTORY, TAX_STATUS, seed_settings,
                          upgrade_founder_text)
from api.models import SiteSetting

ROOT = Path(__file__).resolve().parents[1]
OLD_TAX_STATUS = ("Qi Code Academy, Inc. has applied for 501(c)(3) tax-exempt status. "
                  "Please consult your tax advisor regarding deductibility.")


def test_approved_wording_is_exact():
    assert EIN == "42-5318171"
    assert TAX_STATUS == ("Qi Code Academy, Inc. is a Massachusetts nonprofit corporation and a 501(c)(3) "
                          "tax-exempt organization (EIN 42-5318171). Contributions are tax-deductible to the "
                          "extent allowed by law.")
    assert DONATIONS_NOTICE == ("Qi Code Academy, Inc. is a 501(c)(3) tax-exempt nonprofit. Online donations are "
                                "coming soon while we complete our Massachusetts charity registration. In the "
                                "meantime, there are other ways to get involved.")
    assert ORG_HISTORY.startswith("Qi Code Academy, Inc. was incorporated in 2026 to formalize")


def test_new_settings_seeded_public_and_donations_off(client, db):
    seed_settings()
    db.session.commit()
    settings = client.get("/api/settings").get_json()
    assert settings["tax_status"] == TAX_STATUS
    assert settings["ein"] == EIN
    assert settings["donations_enabled"] == "false"
    assert settings["donations_notice"] == DONATIONS_NOTICE
    assert settings["org_history"] == ORG_HISTORY


def test_seed_upgrades_old_tax_status_but_keeps_edits(db):
    db.session.add(SiteSetting(key="tax_status", value=OLD_TAX_STATUS, is_public=True))
    db.session.commit()
    seed_settings()
    assert upgrade_founder_text() == 1
    db.session.commit()
    row = db.session.query(SiteSetting).filter_by(key="tax_status").one()
    assert row.value == TAX_STATUS
    assert upgrade_founder_text() == 0  # idempotent

    row.value = "Edited by staff"
    db.session.commit()
    upgrade_founder_text()
    assert row.value == "Edited by staff"


def test_frontend_defaults_match_seed():
    en = json.loads((ROOT / "src/front/locales/en.json").read_text())
    assert en["about"]["history"] == ORG_HISTORY
    assert en["donate"]["notice"] == DONATIONS_NOTICE
    assert en["home"]["historyLine"] == "Building on more than 18 years of community teaching in Boston."
    assert en["footer"]["nonprofit"] == "A 501(c)(3) tax-exempt nonprofit organization · EIN {{ein}}"
    assert 'ein: "42-5318171"' in (ROOT / "src/front/js/seo.js").read_text()


def test_eighteen_years_never_describes_the_organization():
    # "18 years" is Joseph's teaching; the organization was incorporated in 2026.
    texts = [ORG_HISTORY, *(v for _, v, _ in DEFAULT_SETTINGS)]
    for path in ROOT.glob("src/front/locales/*.json"):
        texts.append(path.read_text())
    for text in texts:
        assert not re.search(r"(academy|organization|we)\b[^.]{0,40}\b18\s+years\s+old", text, re.I)
        assert not re.search(r"founded\s+(more\s+than\s+)?18\s+years\s+ago", text, re.I)


def test_org_jsonld_has_ein_status_and_founding_date(client, db, app, tmp_path):
    d = tmp_path / "dist"
    d.mkdir()
    (d / "index.html").write_text("<html><head><!--SEO--><!--/SEO--></head><body></body></html>")
    app.config["FRONTEND_DIST_DIR"] = str(d)
    html = client.get("/").get_data(as_text=True)
    assert '"taxID": "42-5318171"' in html
    assert '"nonprofitStatus": "Nonprofit501c3"' in html
    assert '"foundingDate": "2026-09-26"' in html


def test_irs_letter_is_public_and_copied_by_build():
    pdf = ROOT / "src/front/docs/irs-determination-letter.pdf"
    assert pdf.is_file() and pdf.read_bytes().startswith(b"%PDF")
    assert not list(ROOT.glob("*.pdf")), "no PDF copies left in the project root"
    assert '{ from: "src/front/docs", to: "docs" }' in (ROOT / "webpack.common.js").read_text()
    assert '"/docs/irs-determination-letter.pdf"' in (ROOT / "src/front/js/pages/About.js").read_text()
