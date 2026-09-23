"""Admin authentication (JWT in the Authorization header)."""
from functools import wraps

from flask import Blueprint, current_app, g, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from ..extensions import db, limiter
from ..models import User, utcnow
from ..schemas import LoginSchema, UserSchema
from ..utils import APIError, get_json, load

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Used to spend equal time hashing when the email doesn't exist (no user enumeration).
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        try:
            user = db.session.get(User, int(get_jwt_identity()))
        except (TypeError, ValueError):
            user = None
        if not user or not user.is_active:
            raise APIError("Your account is not active.", 401, "unauthorized")
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


@bp.post("/login")
@limiter.limit(lambda: current_app.config["RATELIMIT_LOGIN"])
def login():
    data = load(LoginSchema(), get_json())
    user = db.session.scalar(select(User).where(User.email == data["email"].strip().lower()))
    if user is None:
        from werkzeug.security import check_password_hash
        check_password_hash(_DUMMY_HASH, data["password"])
        raise APIError("Invalid email or password.", 401, "invalid_credentials")
    if not user.check_password(data["password"]) or not user.is_active:
        raise APIError("Invalid email or password.", 401, "invalid_credentials")

    user.last_login_at = utcnow()
    db.session.commit()
    expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    token = create_access_token(identity=str(user.id), additional_claims={"role": "admin"})
    return jsonify({"access_token": token, "token_type": "Bearer",
                    "expires_in": int(expires.total_seconds()), "user": UserSchema().dump(user)})


@bp.get("/me")
@admin_required
def me():
    return jsonify(UserSchema().dump(g.current_user))
