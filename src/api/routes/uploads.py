"""Admin image upload: POST /api/admin/upload (multipart field `file`)."""
import re

from flask import Blueprint, current_app, jsonify, request

from ..services.images import ImageError, process_and_store
from ..utils import APIError
from .auth import admin_required

bp = Blueprint("uploads", __name__, url_prefix="/api/admin")


@bp.post("/upload")
@admin_required
def upload_image():
    file = request.files.get("file")
    if file is None or not file.filename:
        raise APIError("Attach an image in the `file` field.", 400, "validation_error",
                       {"file": ["An image file is required."]})
    data = file.read(current_app.config["MAX_UPLOAD_BYTES"] + 1)
    if len(data) > current_app.config["MAX_UPLOAD_BYTES"]:
        raise APIError("Image is too large (max 10 MB).", 413, "payload_too_large")
    # Optional folder to organize keys, e.g. "gallery", "team", "news".
    folder = request.form.get("folder") or "images"
    if not re.fullmatch(r"[a-z0-9\-]{1,40}", folder):
        raise APIError("Invalid folder name.", 400)
    try:
        result = process_and_store(data, file.filename,
                                   max_width=current_app.config["IMAGE_MAX_WIDTH"], folder=folder)
    except ImageError as exc:
        raise APIError(str(exc), 400, "invalid_image", {"file": [str(exc)]})
    return jsonify(result), 201
