from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


def register_blueprints(app):
    from .public import bp as public_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(public_bp)
