"""Email delivery: SendGrid -> SMTP -> console fallback.

send_email() never raises: a failed email must not break a form submission.
In production, sending happens on a background thread so requests stay fast
(EMAIL_ASYNC); tests and the CLI send inline. send_test_email() sends inline
and reports the real error, for the admin "Send test email" button.

Failures are logged with the provider's actual error message. The SMTP
password is never logged or returned.
"""
import smtplib
import ssl
import threading
from dataclasses import dataclass, field
from email.message import EmailMessage as MIMEMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr

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


def _build(to, subject, text, html=None, reply_to=None, tags=None):
    recipients = [t.strip() for t in ([to] if isinstance(to, str) else to or []) if t and t.strip()]
    if not recipients:
        return None
    return OutgoingEmail(to=recipients, subject=_clean_header(subject), text=text, html=html,
                         reply_to=_clean_header(reply_to) or None, tags=tags or [])


def send_email(to, subject, text, html=None, reply_to=None, tags=None):
    msg = _build(to, subject, text, html, reply_to, tags)
    if not msg:
        return False
    app = current_app._get_current_object()
    if app.config.get("EMAIL_ASYNC", False) and not app.testing:
        threading.Thread(target=_deliver_in_context, args=(app, msg), daemon=True).start()
        return True
    return _safe_deliver(app, msg)


def send_test_email(to, subject, text):
    """Send synchronously. Returns (ok, provider, error_message_or_None)."""
    provider = provider_name()
    msg = _build(to, subject, text)
    if not msg:
        return False, provider, "ADMIN_NOTIFY_EMAIL is not set, so there is no address to send to."
    try:
        ok = bool(_deliver(msg))
    except Exception as exc:  # noqa: BLE001 — report it to the admin
        _log_failure(current_app, msg, exc)
        return False, provider, describe_error(exc)
    if not ok:
        return False, provider, ("No email provider is configured. Set SMTP_HOST, SMTP_PORT, "
                                 "SMTP_USERNAME and SMTP_PASSWORD on the server.")
    return True, provider, None


def provider_name(cfg=None):
    cfg = cfg or current_app.config
    if cfg.get("SENDGRID_API_KEY"):
        return "sendgrid"
    if cfg.get("SMTP_HOST"):
        return "smtp"
    return "console"


def sender_address(cfg=None):
    """The From address actually used by the active provider."""
    cfg = cfg or current_app.config
    return (_smtp_sender(cfg) if provider_name(cfg) == "smtp" else _from(cfg))[1]


def describe_error(exc):
    """A readable one-line description of a delivery error (never includes the password)."""
    if isinstance(exc, smtplib.SMTPResponseException):
        detail = exc.smtp_error.decode(errors="replace") if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
        return f"{type(exc).__name__}: SMTP {exc.smtp_code} {' '.join(detail.split())}"
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        parts = [f"{addr}: {code} {err.decode(errors='replace') if isinstance(err, bytes) else err}"
                 for addr, (code, err) in exc.recipients.items()]
        return f"SMTPRecipientsRefused: {'; '.join(parts)}"
    return f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__


def _log_failure(app, msg, exc):
    cfg = app.config
    app.logger.error("Email delivery failed via %s (host=%s port=%s user=%s): %s | subject=%r to=%s",
                     provider_name(cfg), cfg.get("SMTP_HOST") or "-", cfg.get("SMTP_PORT"),
                     cfg.get("SMTP_USERNAME") or "-", describe_error(exc), msg.subject, msg.to)


def _deliver_in_context(app, msg):
    with app.app_context():
        _safe_deliver(app, msg)


def _safe_deliver(app, msg):
    try:
        return bool(_deliver(msg))
    except Exception as exc:  # noqa: BLE001 — log and move on
        _log_failure(app, msg, exc)
        return False


def _deliver(msg):
    cfg = current_app.config
    provider = provider_name(cfg)
    if provider == "sendgrid":
        return _send_sendgrid(msg, cfg)
    if provider == "smtp":
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
    if not 200 <= resp.status_code < 300:
        raise RuntimeError(f"SendGrid returned HTTP {resp.status_code}: {resp.body!r}")
    return True


def _smtp_sender(cfg):
    """Mailbox hosts (e.g. Network Solutions Professional Email) only relay mail whose From
    is the authenticated mailbox, so when the login is an email address, send as it
    (keeping MAIL_FROM's display name)."""
    name, addr = _from(cfg)
    username = (cfg.get("SMTP_USERNAME") or "").strip()
    if "@" in username and username.lower() != (addr or "").lower():
        addr = username
    return name, addr


def _send_smtp(msg, cfg):
    name, addr = _smtp_sender(cfg)
    mime = MIMEMessage()
    mime["Subject"] = msg.subject
    mime["From"] = formataddr((name, addr))
    mime["To"] = ", ".join(msg.to)
    mime["Date"] = formatdate(localtime=True)
    mime["Message-ID"] = make_msgid(domain=addr.rpartition("@")[2] or None)
    reply_to = msg.reply_to or cfg.get("MAIL_REPLY_TO")
    if reply_to:
        mime["Reply-To"] = reply_to
    mime.set_content(msg.text)
    if msg.html:
        mime.add_alternative(msg.html, subtype="html")

    host, port = cfg["SMTP_HOST"].strip(), int(cfg.get("SMTP_PORT") or 587)
    # Port 465 is implicit SSL; anything else (normally 587) uses STARTTLS.
    use_ssl = bool(cfg.get("SMTP_USE_SSL")) or port == 465
    context = ssl.create_default_context()
    if use_ssl:
        server_cm = smtplib.SMTP_SSL(host, port, timeout=20, context=context)
    else:
        server_cm = smtplib.SMTP(host, port, timeout=20)
    with server_cm as server:
        server.ehlo()
        if not use_ssl and cfg.get("SMTP_USE_TLS", True):
            server.starttls(context=context)
            server.ehlo()
        if cfg.get("SMTP_USERNAME"):
            server.login(cfg["SMTP_USERNAME"].strip(), cfg.get("SMTP_PASSWORD") or "")
        server.send_message(mime, from_addr=addr, to_addrs=msg.to)
    return True


def _send_console(msg, cfg):
    if cfg.get("IS_PRODUCTION"):
        current_app.logger.warning("No email provider configured (SMTP_HOST is not set); email NOT sent: %s -> %s",
                                   msg.subject, msg.to)
        return False
    bar = "=" * 70
    print(f"\n{bar}\n[DEV EMAIL — not sent]\nTo: {', '.join(msg.to)}\n"
          f"Reply-To: {msg.reply_to or '-'}\nSubject: {msg.subject}\n{'-' * 70}\n{msg.text}\n{bar}\n",
          flush=True)
    return True
