"""Application configuration.

Every secret and deployment-specific value comes from environment variables
(see .env.example). Nothing sensitive is hard-coded; development falls back to
throwaway values so the app can boot in a fresh Codespace.
"""
import os
import secrets
from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _bool(name, default=False):
    val = os.getenv(name)
    if val is None or val == "":
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _int(name, default):
    val = os.getenv(name)
    try:
        return int(val) if val not in (None, "") else default
    except ValueError:
        return default


def _list(name):
    return [v.strip().rstrip("/") for v in (os.getenv(name) or "").split(",") if v.strip()]


def _database_url():
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        instance = REPO_ROOT / "instance"
        instance.mkdir(exist_ok=True)
        return f"sqlite:///{instance / 'dev.db'}"
    # Render/Heroku/Railway may hand out postgres:// which SQLAlchemy 2 no longer accepts.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    ENV_NAME = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development").lower()
    IS_PRODUCTION = ENV_NAME == "production"
    TESTING = False

    # --- Core secrets -------------------------------------------------------
    # In development a random key is generated per process if none is set
    # (sessions/JWTs then reset on restart, which is fine locally).
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=_int("JWT_EXPIRES_HOURS", 8))
    JWT_TOKEN_LOCATION = ["headers"]

    # --- Database -----------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- URLs / CORS --------------------------------------------------------
    # SITE_URL falls back to Railway's auto-provided public domain, then localhost.
    SITE_URL = (os.getenv("SITE_URL")
                or (f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}" if os.getenv("RAILWAY_PUBLIC_DOMAIN") else "")
                or "http://localhost:3001").rstrip("/")
    CORS_ORIGINS = _list("CORS_ORIGINS")
    # Regexes allowed in development only (Codespaces forwarded ports + localhost).
    DEV_CORS_ORIGIN_PATTERNS = [
        r"https://.*\.app\.github\.dev",
        r"https://.*\.githubpreview\.dev",
        r"http://localhost(:\d+)?",
        r"http://127\.0\.0\.1(:\d+)?",
    ]
    FRONTEND_DIST_DIR = os.getenv("FRONTEND_DIST_DIR") or str(REPO_ROOT / "dist_manual")

    # --- Cookies (Flask-Admin session login) --------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_PRODUCTION

    # --- Rate limiting ------------------------------------------------------
    RATELIMIT_ENABLED = _bool("RATELIMIT_ENABLED", True)
    RATELIMIT_STORAGE_URI = (os.getenv("RATELIMIT_STORAGE_URI") or "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_FORMS = (os.getenv("RATELIMIT_FORMS") or "5 per minute;30 per hour")
    RATELIMIT_DONATIONS = (os.getenv("RATELIMIT_DONATIONS") or "10 per minute;60 per hour")
    RATELIMIT_LOGIN = (os.getenv("RATELIMIT_LOGIN") or "10 per minute;50 per hour")

    # --- Uploads ------------------------------------------------------------
    MAX_UPLOAD_BYTES = 10 * 1024 * 1024
    # Request body cap: 10 MB image plus multipart overhead.
    MAX_CONTENT_LENGTH = MAX_UPLOAD_BYTES + 512 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER") or str(REPO_ROOT / "uploads")
    IMAGE_MAX_WIDTH = 1920
    R2_ACCOUNT_ID = (os.getenv("R2_ACCOUNT_ID") or "")
    R2_ACCESS_KEY_ID = (os.getenv("R2_ACCESS_KEY_ID") or "")
    R2_SECRET_ACCESS_KEY = (os.getenv("R2_SECRET_ACCESS_KEY") or "")
    R2_BUCKET = (os.getenv("R2_BUCKET") or "")
    R2_PUBLIC_URL = (os.getenv("R2_PUBLIC_URL") or "").rstrip("/")

    # --- Email --------------------------------------------------------------
    MAIL_FROM = (os.getenv("MAIL_FROM") or "Qi Code Academy <no-reply@qicodeacademy.org>")
    MAIL_REPLY_TO = (os.getenv("MAIL_REPLY_TO") or "")
    ADMIN_NOTIFY_EMAIL = (os.getenv("ADMIN_NOTIFY_EMAIL") or "")
    SENDGRID_API_KEY = (os.getenv("SENDGRID_API_KEY") or "")
    SMTP_HOST = (os.getenv("SMTP_HOST") or "")
    SMTP_PORT = _int("SMTP_PORT", 587)
    SMTP_USERNAME = (os.getenv("SMTP_USERNAME") or "")
    SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD") or "")
    SMTP_USE_TLS = _bool("SMTP_USE_TLS", True)
    SMTP_USE_SSL = _bool("SMTP_USE_SSL", False)
    # Send on a background thread so form requests stay fast (default on in production).
    EMAIL_ASYNC = _bool("EMAIL_ASYNC", IS_PRODUCTION)

    # --- Stripe -------------------------------------------------------------
    STRIPE_SECRET_KEY = (os.getenv("STRIPE_SECRET_KEY") or "")
    STRIPE_WEBHOOK_SECRET = (os.getenv("STRIPE_WEBHOOK_SECRET") or "")
    STRIPE_SUCCESS_URL = (os.getenv("STRIPE_SUCCESS_URL") or "")
    STRIPE_CANCEL_URL = (os.getenv("STRIPE_CANCEL_URL") or "")
    STRIPE_CURRENCY = (os.getenv("STRIPE_CURRENCY") or "usd")
    DONATION_MIN_CENTS = _int("DONATION_MIN_CENTS", 100)          # $1
    DONATION_MAX_CENTS = _int("DONATION_MAX_CENTS", 2_500_000)    # $25,000

    # --- Compression (Flask-Compress: brotli/gzip for HTML, JSON, JS, CSS, SVG) ---
    COMPRESS_MIMETYPES = ["text/html", "text/css", "text/plain", "text/xml", "text/calendar", "application/json",
                          "application/javascript", "text/javascript", "application/xml", "image/svg+xml"]
    COMPRESS_MIN_SIZE = 1024

    # --- Misc ---------------------------------------------------------------
    ORG_NAME = "Qi Code Academy"
    ORG_LEGAL_NAME = "Qi Code Academy, Inc."
    ORG_TIMEZONE = "America/New_York"

    @classmethod
    def validate(cls, config):
        """Refuse to boot production with missing critical secrets."""
        if config.get("IS_PRODUCTION") and not config.get("TESTING"):
            missing = [k for k in ("SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL")
                       if not os.getenv(k)]
            if missing:
                raise RuntimeError(
                    f"Missing required environment variables in production: {', '.join(missing)}")


class TestingConfig(Config):
    TESTING = True
    ENV_NAME = "testing"
    IS_PRODUCTION = False
    SECRET_KEY = "test-secret-key-not-for-production-use-000000"
    JWT_SECRET_KEY = "test-jwt-secret-key-not-for-production-000000"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    SENDGRID_API_KEY = ""
    SMTP_HOST = ""
    EMAIL_ASYNC = False
    ADMIN_NOTIFY_EMAIL = "admin-notify@example.org"
    R2_ACCOUNT_ID = R2_ACCESS_KEY_ID = R2_SECRET_ACCESS_KEY = R2_BUCKET = R2_PUBLIC_URL = ""
    STRIPE_SECRET_KEY = "sk_test_dummy"
    STRIPE_WEBHOOK_SECRET = "whsec_test_dummy"
    STRIPE_SUCCESS_URL = "http://localhost:3001/donate/thank-you"
    STRIPE_CANCEL_URL = "http://localhost:3001/donate/cancelled"
    WTF_CSRF_ENABLED = False


def get_config():
    return TestingConfig if os.getenv("APP_ENV") == "testing" else Config
