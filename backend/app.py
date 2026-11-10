from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db
from database.seed import seed_categories, seed_preliminary_rules
from models import AuditLog, Category, Declaration, Inspection, Rule, User
from routes.dashboard import dashboard_bp
from routes.health import health_bp
from routes.inspection import inspection_bp
from routes.rules import rules_bp
from routes.auth import auth_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_categories(db)
        seed_preliminary_rules(db)
        if app.config["ADMIN_EMAIL"] and app.config["ADMIN_PASSWORD"] and not User.query.filter_by(email=app.config["ADMIN_EMAIL"]).first():
            db.session.add(User(
                email=app.config["ADMIN_EMAIL"],
                password_hash=generate_password_hash(app.config["ADMIN_PASSWORD"]),
                role="admin",
            ))
            db.session.commit()

    api_prefix = app.config["API_PREFIX"]
    app.register_blueprint(health_bp, url_prefix=api_prefix)
    app.register_blueprint(inspection_bp, url_prefix=api_prefix)
    app.register_blueprint(dashboard_bp, url_prefix=api_prefix)
    app.register_blueprint(rules_bp, url_prefix=api_prefix)
    app.register_blueprint(auth_bp, url_prefix=api_prefix)

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(413)
    def handle_payload_too_large(error):
        return jsonify({"error": "Uploaded request exceeds the 10 MB limit."}), 413

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=app.config["PORT"], debug=app.config["DEBUG"])
