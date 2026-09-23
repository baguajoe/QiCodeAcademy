"""File storage: Cloudflare R2 (S3 API via boto3) or local disk fallback.

R2 is used only when all of R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
R2_BUCKET and R2_PUBLIC_URL are set; otherwise files go to UPLOAD_FOLDER and are
served by Flask at /uploads/<key>.
"""
from pathlib import Path

from flask import current_app

_R2_KEYS = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_PUBLIC_URL")
_client_cache = {}


def r2_enabled(config=None):
    config = config or current_app.config
    return all(config.get(k) for k in _R2_KEYS)


def _r2_client(config):
    key = (config["R2_ACCOUNT_ID"], config["R2_ACCESS_KEY_ID"])
    if key not in _client_cache:
        import boto3
        from botocore.config import Config as BotoConfig
        _client_cache[key] = boto3.client(
            "s3",
            endpoint_url=f"https://{config['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=config["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=config["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
            config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
        )
    return _client_cache[key]


def save_bytes(key, data, content_type):
    """Store bytes under `key` (e.g. 'images/2026/09/abc.webp'); return its public URL."""
    config = current_app.config
    key = key.lstrip("/")
    if ".." in Path(key).parts:
        raise ValueError("Invalid storage key.")
    if r2_enabled(config):
        _r2_client(config).put_object(
            Bucket=config["R2_BUCKET"], Key=key, Body=data, ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable")
        return f"{config['R2_PUBLIC_URL']}/{key}"

    path = Path(config["UPLOAD_FOLDER"]) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return f"/uploads/{key}"


def backend_name():
    return "r2" if r2_enabled() else "local"
