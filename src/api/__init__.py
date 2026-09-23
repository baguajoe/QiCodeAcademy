"""Qi Code Academy API — Flask application factory."""
import logging
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import REPO_ROOT, Config, get_config
from .extensions import cors, db, jwt, limiter, migrate
from .models import ModelRuleError
from .utils import APIError, error_response


def create_app(config_object=None, **overrides):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object or get_config())
    app.config.update(overrides)
    Config.validate(app.config)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Render (and Codespaces) sit behind one proxy hop: trust X-Forwarded-* once
    # so rate limiting sees the real client IP and url_for builds https URLs.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db, directory=str(REPO_ROOT / "migrations"), render_as_batch=True)
    jwt.init_app(app)
    limiter.init_app(app)
    _init_cors(app)

    from .routes import register_blueprints
    register_blueprints(app)

    from .commands import register_commands
    register_commands(app)

    from .admin_panel import init_admin_panel
    init_admin_panel(app)

    _register_error_handlers(app)
    _register_jwt_handlers(app)
    _register_static(app)
    return app


def _init_cors(app):
    if app.config["IS_PRODUCTION"]:
        origins = app.config["CORS_ORIGINS"] or [app.config["SITE_URL"]]
    else:
        origins = app.config["CORS_ORIGINS"] + app.config["DEV_CORS_ORIGIN_PATTERNS"]
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": origins}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=600,
    )


def _wants_json():
    return request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json"


def _register_error_handlers(app):
    @app.errorhandler(APIError)
    def _api_error(err):
        return error_response(err.message, err.status, err.error, err.errors)

    @app.errorhandler(ModelRuleError)
    def _model_rule(err):
        db.session.rollback()
        return error_response(str(err), 400, "rule_violation")

    @app.errorhandler(IntegrityError)
    def _integrity(err):
        db.session.rollback()
        app.logger.warning("IntegrityError: %s", err.orig)
        return error_response("That record conflicts with existing data (duplicate or in use).",
                              409, "conflict")

    @app.errorhandler(HTTPException)
    def _http(err):
        if not _wants_json():
            return err
        names = {413: "Upload too large (max 10 MB).",
                 429: "Too many requests. Please wait a moment and try again."}
        return error_response(names.get(err.code, err.description), err.code,
                              (err.name or "error").lower().replace(" ", "_"))

    @app.errorhandler(Exception)
    def _unhandled(err):
        db.session.rollback()
        app.logger.exception("Unhandled error")
        if not _wants_json():
            raise err
        return error_response("Something went wrong on our end.", 500, "server_error")


def _register_jwt_handlers(app):
    @jwt.unauthorized_loader
    def _missing(reason):
        return error_response("Authentication required.", 401, "unauthorized")

    @jwt.invalid_token_loader
    def _invalid(reason):
        return error_response("Invalid token.", 401, "invalid_token")

    @jwt.expired_token_loader
    def _expired(header, payload):
        return error_response("Session expired. Please log in again.", 401, "token_expired")


def _register_static(app):
    upload_dir = Path(app.config["UPLOAD_FOLDER"])

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        # Local-disk fallback when R2 isn't configured.
        resp = send_from_directory(upload_dir, filename, max_age=60 * 60 * 24 * 30)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    dist = Path(app.config["FRONTEND_DIST_DIR"])

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path=""):
        # Serve the built React app (webpack output) with SPA fallback.
        if path.startswith("api/"):
            return error_response("Not found.", 404, "not_found")
        if path and (dist / path).is_file():
            return send_from_directory(dist, path)
        if (dist / "index.html").is_file():
            return send_from_directory(dist, "index.html")
        return jsonify({"name": "Qi Code Academy API", "status": "ok",
                        "docs": "See API.md", "frontend": "not built yet"})
