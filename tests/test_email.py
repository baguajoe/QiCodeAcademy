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
    db.session.add(SiteSetting(key="tax_status", value="Qi Code Academy, Inc. is a 501(c)(3) tax-exempt organization."))
    d = Donation(amount_cents=2500, designation="youth", donor_name="Kim",
                 donor_email="kim@example.org", status="completed", recurring=True)
    db.session.add(d)
    db.session.commit()
    notifications.donation_thank_you(d)
    assert "$25.00" in outbox[0].text and "Qi Code Academy, Inc. is a 501(c)(3) tax-exempt organization." in outbox[0].text
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


def _smtp_app(app, **kw):
    app.config.update({"SMTP_HOST": "netsol-smtp-oxcs.hostingplatform.com", "SMTP_PORT": 587,
                       "SMTP_USERNAME": "info@qicodeacademy.org", "SMTP_PASSWORD": "secret-pw",
                       "SMTP_USE_TLS": True, "SMTP_USE_SSL": False,
                       "MAIL_FROM": "Qi Code Academy <no-reply@qicodeacademy.org>", **kw})


def test_smtp_587_starttls_full_address_login_and_mailbox_sender(app):
    _smtp_app(app)
    with mock.patch("smtplib.SMTP") as smtp, mock.patch("smtplib.SMTP_SSL") as smtp_ssl:
        assert email_service.send_email("admin@example.org", "Hi", "text", reply_to="person@example.org") is True
        smtp.assert_called_once()
        assert smtp.call_args[0][:2] == ("netsol-smtp-oxcs.hostingplatform.com", 587)
        smtp_ssl.assert_not_called()
        server = smtp.return_value.__enter__.return_value
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("info@qicodeacademy.org", "secret-pw")
        sent = server.send_message.call_args
        assert sent.kwargs["from_addr"] == "info@qicodeacademy.org"
        assert sent[0][0]["From"] == "Qi Code Academy <info@qicodeacademy.org>"
        assert sent[0][0]["Reply-To"] == "person@example.org"


def test_smtp_465_uses_ssl(app):
    _smtp_app(app, SMTP_PORT=465)
    with mock.patch("smtplib.SMTP") as smtp, mock.patch("smtplib.SMTP_SSL") as smtp_ssl:
        assert email_service.send_email("a@example.org", "Hi", "text") is True
        smtp.assert_not_called()
        assert smtp_ssl.call_args[0][:2] == ("netsol-smtp-oxcs.hostingplatform.com", 465)
        server = smtp_ssl.return_value.__enter__.return_value
        server.starttls.assert_not_called()
        server.login.assert_called_once_with("info@qicodeacademy.org", "secret-pw")


def test_smtp_failure_logs_real_error_without_password(app, caplog):
    import smtplib
    _smtp_app(app)
    with mock.patch("smtplib.SMTP") as smtp:
        server = smtp.return_value.__enter__.return_value
        server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.8 Authentication failed")
        assert email_service.send_email("a@example.org", "Hi", "text") is False
    assert "SMTP 535 5.7.8 Authentication failed" in caplog.text
    assert "secret-pw" not in caplog.text


def test_failed_email_still_saves_every_form(client, db, monkeypatch, make_program):
    from api.models import ContactMessage, Volunteer, WellnessDayInterest, WellnessDayPartner

    def boom(msg):
        raise OSError("connection refused")
    monkeypatch.setattr(email_service, "_deliver", boom)
    assert client.post("/api/contact", json={"name": "a", "email": "a@x.org", "message": "m"}).status_code == 201
    assert client.post("/api/volunteers", json={"name": "V", "email": "v@x.org", "roles": ["event_help"]}).status_code == 201
    assert client.post("/api/wellness-day/interest", json={"name": "S", "email": "s@x.org", "consent_to_contact": True,
                                                           "activities": ["acupuncture"]}).status_code == 201
    assert db.session.query(ContactMessage).count() == 1
    assert db.session.query(Volunteer).count() == 1
    assert db.session.query(WellnessDayInterest).count() == 1
    assert db.session.query(WellnessDayPartner).count() == 0


def test_notification_bug_still_returns_201(client, monkeypatch):
    monkeypatch.setattr(notifications, "_render", mock.Mock(side_effect=ValueError("bad template")))
    assert client.post("/api/contact", json={"name": "a", "email": "a@x.org", "message": "m"}).status_code == 201


def test_admin_notifications_reply_to_submitter(client, outbox, make_program):
    client.post("/api/volunteers", json={"name": "V", "email": "v@example.org", "roles": ["event_help"]})
    client.post("/api/wellness-day/interest", json={"name": "S", "email": "s@example.org", "consent_to_contact": True,
                                                    "activities": ["acupuncture"]})
    p = make_program(division="senior")
    client.post("/api/registrations", json={**SENIOR, "program_id": p.id})
    admin = [m for m in outbox if m.to == ["admin-notify@example.org"]]
    assert [m.reply_to for m in admin] == ["v@example.org", "s@example.org", SENIOR["email"]]


def test_admin_send_test_email_success(app, client, auth_headers, outbox):
    _smtp_app(app)
    res = client.post("/api/admin/email/test", headers=auth_headers, json={})
    body = res.get_json()
    assert res.status_code == 200 and body["ok"] is True, body
    assert outbox[-1].to == ["admin-notify@example.org"] and "Test email" in outbox[-1].subject


def test_admin_send_test_email_shows_exact_error(app, client, auth_headers):
    import smtplib
    _smtp_app(app, EMAIL_ASYNC=True)  # the test button always sends inline
    with mock.patch("smtplib.SMTP") as smtp:
        smtp.return_value.__enter__.return_value.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"5.7.8 Authentication failed")
        body = client.post("/api/admin/email/test", headers=auth_headers, json={}).get_json()
    assert body["ok"] is False
    assert "SMTP 535 5.7.8 Authentication failed" in body["error"]
    assert body["settings"]["smtp_security"] == "STARTTLS" and body["settings"]["smtp_password_set"] is True
    assert "secret-pw" not in str(body)


def test_admin_send_test_email_requires_admin(client):
    assert client.post("/api/admin/email/test", json={}).status_code == 401
