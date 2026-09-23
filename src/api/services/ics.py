"""Minimal RFC 5545 calendar file for a single event (no extra dependency)."""
from datetime import timedelta
from urllib.parse import urlparse

from ..models import utcnow

VTIMEZONE_NY = """BEGIN:VTIMEZONE
TZID:America/New_York
X-LIC-LOCATION:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE"""


def _escape(text):
    return (str(text or "").replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n"))


def _fold(line):
    """Fold lines longer than 75 octets (RFC 5545 §3.1)."""
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > 75:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n".join(out)


def event_to_ics(event, site_url, org_name="Qi Code Academy"):
    host = urlparse(site_url).hostname or "qicodeacademy.org"
    start = event.start_datetime
    end = event.end_datetime or (start + timedelta(hours=1))
    fmt = "%Y%m%dT%H%M%S"
    location = ", ".join(p for p in (event.location, event.neighborhood, "Boston, MA") if p)
    url = f"{site_url}/events/{event.slug}"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{org_name}//Events//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        *VTIMEZONE_NY.split("\n"),
        "BEGIN:VEVENT",
        f"UID:event-{event.id}@{host}",
        f"DTSTAMP:{utcnow().strftime(fmt)}Z",
        f"DTSTART;TZID=America/New_York:{start.strftime(fmt)}",
        f"DTEND;TZID=America/New_York:{end.strftime(fmt)}",
        f"SUMMARY:{_escape(event.title)}",
        f"DESCRIPTION:{_escape((event.description or '') + chr(10) + chr(10) + url)}",
        f"LOCATION:{_escape(location)}",
        f"URL:{url}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
