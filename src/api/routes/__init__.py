from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


def register_blueprints(app):
    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .public import bp as public_bp
    from .uploads import bp as uploads_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(uploads_bp)
