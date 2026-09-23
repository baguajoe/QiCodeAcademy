from unittest import mock

from api.models import Donation, Registration, SiteSetting
from api.services import email as email_service
from api.services import notifications

from .test_public import SENIOR, YOUTH


def test_youth_registration_emails_guardian_and_admin(client, outbox, make_program):
    p = make_program(title="Robotics", schedule="Saturdays 10-12")
    client.post("/api/registrations", json={**YOUTH, "program_id": p.id})
    assert len(outbox) == 2
    family, admin = outbox
    assert family.to == ["pat@example.org"]
    assert "Registration received: Robotics" in family.subject
    assert "Sam Lee" in family.text and "Saturdays 10-12" in family.text
    assert admin.to == ["admin-notify@example.org"]
    assert "youth registration (pending)" in admin.subject


def test_waitlist_email(client, outbox, make_program):
    p = make_program(capacity=0)
    client.post("/api/registrations", json={**YOUTH, "program_id": p.id})
    assert outbox[0].subject.startswith("You're on the waitlist")


def test_senior_without_email_only_notifies_admin(client, outbox, make_program):
    p = make_program(division="senior")
    data = {**SENIOR, "program_id": p.id}
    del data["email"]
    client.post("/api/registrations", json=data)
    assert [m.to for m in outbox] == [["admin-notify@example.org"]]


def test_honeypot_sends_nothing(client, outbox):
    client.post("/api/contact", json={"name": "x", "email": "x@x.org", "message": "m", "website": "spam"})
    assert outbox == []


def test_contact_escapes_html_and_sets_reply_to(client, outbox):
    client.post("/api/contact", json={"name": "<b>Eve</b>", "email": "eve@example.org",
                                      "subject": "Hi\r\nBcc: victim@x.org", "message": "<script>x</script>"})
    ack, admin = outbox
    assert ack.to == ["eve@example.org"]
    assert "<script>" not in admin.html and "&lt;script&gt;" in admin.html
    assert "\n" not in admin.subject and "\r" not in admin.subject
    assert admin.reply_to == "eve@example.org"


def test_volunteer_and_research_emails(client, outbox):
    client.post("/api/volunteers", json={"name": "V", "email": "v@example.org", "roles": ["senior_tech_tutor"]})
    assert outbox[0].to == ["v@example.org"] and "Tech tutor for seniors" in outbox[0].text
    outbox.clear()
    client.post("/api/research/inquiries", json={"name": "R", "institution": "U", "email": "r@u.edu"})
    assert [m.to for m in outbox] == [["r@u.edu"], ["admin-notify@example.org"]]
    outbox.clear()
    client.post("/api/research/interest", json={"name": "Q", "email_or_phone": "617-555-0100",
                                                "consent_to_contact": True})
    assert [m.to for m in outbox] == [["admin-notify@example.org"]]  # phone only: no ack email
    assert "617" not in outbox[0].text  # admin email omits contact details


def test_admin_confirming_registration_emails_family(client, db, outbox, auth_headers, make_program):
    p = make_program()
    reg = Registration(**{**YOUTH, "program_id": p.id})
    db.session.add(reg)
    db.session.commit()
    client.patch(f"/api/admin/registrations/{reg.id}", headers=auth_headers, json={"status": "confirmed"})
    assert len(outbox) == 1 and outbox[0].subject.startswith("You're confirmed")
    client.patch(f"/api/admin/registrations/{reg.id}", headers=auth_headers, json={"admin_notes": "x"})
    assert len(outbox) == 1  # no repeat


def test_donation_thank_you_uses_tax_status(app, db, outbox):
    db.session.add(SiteSetting(key="tax_status", value="Applied for 501(c)(3) status."))
    d = Donation(amount_cents=2500, designation="youth", donor_name="Kim",
                 donor_email="kim@example.org", status="completed", recurring=True)
    db.session.add(d)
    db.session.commit()
    notifications.donation_thank_you(d)
    assert "$25.00" in outbox[0].text and "Applied for 501(c)(3) status." in outbox[0].text
    assert "Monthly" in outbox[0].text


def test_email_failure_does_not_break_request(client, monkeypatch, make_program):
    def boom(msg):
        raise RuntimeError("provider down")
    monkeypatch.setattr(email_service, "_deliver", boom)
    assert client.post("/api/contact", json={"name": "a", "email": "a@x.org", "message": "m"}).status_code == 201


def test_console_fallback_prints(app, capsys):
    assert email_service.send_email("a@example.org", "Hello", "Body text") is True
    assert "[DEV EMAIL" in capsys.readouterr().out


def test_sendgrid_used_when_configured(app):
    app.config["SENDGRID_API_KEY"] = "SG.test"
    with mock.patch("sendgrid.SendGridAPIClient") as sg:
        sg.return_value.send.return_value.status_code = 202
        assert email_service.send_email("a@example.org", "Hi", "text", "<p>html</p>") is True
        mail = sg.return_value.send.call_args[0][0].get()
        assert mail["personalizations"][0]["to"][0]["email"] == "a@example.org"
        assert mail["subject"] == "Hi"


def test_smtp_used_when_configured(app):
    app.config.update(SMTP_HOST="smtp.example.org", SMTP_USERNAME="u", SMTP_PASSWORD="p")
    with mock.patch("smtplib.SMTP") as smtp:
        assert email_service.send_email("a@example.org", "Hi", "text") is True
        server = smtp.return_value.__enter__.return_value
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("u", "p")
        assert server.send_message.call_args[0][0]["To"] == "a@example.org"
