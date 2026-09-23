"""Shared helpers: JSON errors, validation, honeypot, pagination, time, CSV."""
import csv
import io
from datetime import datetime, timezone
from functools import wraps
from zoneinfo import ZoneInfo

from flask import current_app, jsonify, request
from marshmallow import ValidationError

HONEYPOT_FIELD = "website"


class APIError(Exception):
    def __init__(self, message, status=400, error="bad_request", errors=None):
        super().__init__(message)
        self.message, self.status, self.error, self.errors = message, status, error, errors


def error_response(message, status=400, error="bad_request", errors=None):
    body = {"error": error, "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status


def get_json():
    """Request body as a dict (JSON or form-encoded), never None."""
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict() if request.form else {}
    if not isinstance(data, dict):
        raise APIError("Request body must be a JSON object.")
    return data


def load(schema, data, partial=False):
    """Validate with a marshmallow schema, raising a 400 APIError on failure."""
    try:
        return schema.load(data, partial=partial)
    except ValidationError as err:
        raise APIError("Please correct the highlighted fields.", 400, "validation_error",
                       err.messages)


def honeypot_triggered(data):
    return bool(str(data.get(HONEYPOT_FIELD) or "").strip())


def honeypot(success_body, status=201):
    """Decorator for public form endpoints: if the hidden 'website' field is filled,
    pretend success and store nothing."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or (request.form.to_dict() if request.form else {})
            if isinstance(data, dict) and honeypot_triggered(data):
                current_app.logger.info("Honeypot triggered on %s; discarding.", request.path)
                return jsonify(success_body), status
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def parse_bool(value, default=None):
    if value is None or value == "":
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def parse_list(value):
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def page_args(default_per_page=12, max_per_page=100):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get("per_page", default_per_page))
    except ValueError:
        per_page = default_per_page
    return page, min(max(per_page, 1), max_per_page)


def paginate(query, schema, default_per_page=12, max_per_page=100):
    from .extensions import db
    page, per_page = page_args(default_per_page, max_per_page)
    result = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return {
        "items": schema.dump(result.items, many=True),
        "page": result.page,
        "per_page": result.per_page,
        "total": result.total,
        "pages": result.pages,
    }


# --- Time ------------------------------------------------------------------
def org_tz():
    return ZoneInfo(current_app.config.get("ORG_TIMEZONE", "America/New_York"))


def local_now():
    """Current Boston wall-clock time as a naive datetime (matches Event storage)."""
    return datetime.now(org_tz()).replace(tzinfo=None)


def to_local_naive(dt):
    """Normalize an incoming datetime to naive Boston wall-clock time."""
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(org_tz()).replace(tzinfo=None)


def iso_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


# --- CSV -------------------------------------------------------------------
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(v) for v in value)
    value = str(value)
    # Neutralize spreadsheet formula injection.
    if value.startswith(_FORMULA_PREFIXES):
        value = "'" + value
    return value


def csv_response(filename, header, rows):
    from flask import Response
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_csv_safe(v) for v in row])
    return Response(
        "﻿" + buf.getvalue(),  # BOM so Excel opens UTF-8 correctly
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"',
                 "Cache-Control": "no-store"},
    )
