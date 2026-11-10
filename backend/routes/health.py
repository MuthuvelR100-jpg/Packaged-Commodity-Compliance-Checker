from flask import Blueprint, current_app, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify({
        "status": "ok",
        "phase": 4,
        "service": "compliance-api",
        "environment": "development" if current_app.config["DEBUG"] else "production",
    })
