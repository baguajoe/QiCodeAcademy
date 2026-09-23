"""Email delivery: SendGrid -> SMTP -> console fallback.

send_email() never raises: a failed email must not break a form submission.
In production, sending happens on a background thread so requests stay fast
(EMAIL_ASYNC); tests and the CLI send inline.
"""
import smtplib
import threading
from dataclasses import dataclass, field
from email.message import EmailMessage as MIMEMessage
from email.utils import formataddr, parseaddr

from flask import current_app


@dataclass
class OutgoingEmail:
    to: list
    subject: str
    text: str
    html: str = None
    reply_to: str = None
    tags: list = field(default_factory=list)


def _clean_header(value):
    return " ".join(str(value or "").split())[:250]


def send_email(to, subject, text, html=None, reply_to=None, tags=None):
    recipients = [t.strip() for t in ([to] if isinstance(to, str) else to or []) if t and t.strip()]
    if not recipients:
        return False
    msg = OutgoingEmail(to=recipients, subject=_clean_header(subject), text=text, html=html,
                        reply_to=_clean_header(reply_to) or None, tags=tags or [])
    app = current_app._get_current_object()
    if app.config.get("EMAIL_ASYNC", False) and not app.testing:
        threading.Thread(target=_deliver_in_context, args=(app, msg), daemon=True).start()
        return True
    return _safe_deliver(app, msg)


def _deliver_in_context(app, msg):
    with app.app_context():
        _safe_deliver(app, msg)


def _safe_deliver(app, msg):
    try:
        return bool(_deliver(msg))
    except Exception:  # noqa: BLE001 — log and move on
        app.logger.exception("Email delivery failed: %s -> %s", msg.subject, msg.to)
        return False


def _deliver(msg):
    cfg = current_app.config
    if cfg.get("SENDGRID_API_KEY"):
        return _send_sendgrid(msg, cfg)
    if cfg.get("SMTP_HOST"):
        return _send_smtp(msg, cfg)
    return _send_console(msg, cfg)


def _from(cfg):
    name, addr = parseaddr(cfg["MAIL_FROM"])
    return name or cfg.get("ORG_NAME", ""), addr


def _send_sendgrid(msg, cfg):
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import From, Mail, ReplyTo, To

    name, addr = _from(cfg)
    mail = Mail(from_email=From(addr, name), to_emails=[To(t) for t in msg.to],
                subject=msg.subject, plain_text_content=msg.text, html_content=msg.html)
    reply_to = msg.reply_to or cfg.get("MAIL_REPLY_TO")
    if reply_to:
        mail.reply_to = ReplyTo(reply_to)
    sg = SendGridAPIClient(cfg["SENDGRID_API_KEY"])
    sg.client.timeout = 15
    resp = sg.send(mail)
    return 200 <= resp.status_code < 300


def _send_smtp(msg, cfg):
    mime = MIMEMessage()
    mime["Subject"] = msg.subject
    mime["From"] = formataddr(_from(cfg))
    mime["To"] = ", ".join(msg.to)
    reply_to = msg.reply_to or cfg.get("MAIL_REPLY_TO")
    if reply_to:
        mime["Reply-To"] = reply_to
    mime.set_content(msg.text)
    if msg.html:
        mime.add_alternative(msg.html, subtype="html")

    smtp_cls = smtplib.SMTP_SSL if cfg.get("SMTP_USE_SSL") else smtplib.SMTP
    with smtp_cls(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15) as server:
        if cfg.get("SMTP_USE_TLS") and not cfg.get("SMTP_USE_SSL"):
            server.starttls()
        if cfg.get("SMTP_USERNAME"):
            server.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
        server.send_message(mime)
    return True


def _send_console(msg, cfg):
    if cfg.get("IS_PRODUCTION"):
        current_app.logger.warning("No email provider configured; email NOT sent: %s -> %s",
                                   msg.subject, msg.to)
        return False
    bar = "=" * 70
    print(f"\n{bar}\n[DEV EMAIL — not sent]\nTo: {', '.join(msg.to)}\n"
          f"Reply-To: {msg.reply_to or '-'}\nSubject: {msg.subject}\n{'-' * 70}\n{msg.text}\n{bar}\n",
          flush=True)
    return True
