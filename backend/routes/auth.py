from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash

from extensions import db
from models.user import User
from services.auth_service import admin_required, authenticate, current_user


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or not email.strip() or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = authenticate(email, password)
    if user is None:
        return jsonify({"error": "Invalid email or password."}), 401
    session.clear()
    session["user_id"] = user.id
    return jsonify({"message": "Login successful.", "user": {"id": user.id, "email": user.email, "role": user.role}})


@auth_bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logout successful."})


@auth_bp.get("/auth/me")
def me():
    user = current_user()
    if user is None:
        return jsonify({"user": None}), 200
    return jsonify({"user": {"id": user.id, "email": user.email, "role": user.role}})


@auth_bp.post("/auth/users")
@admin_required
def create_user():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")
    role = payload.get("role", "inspector")
    if not isinstance(email, str) or not isinstance(password, str) or len(password) < 12:
        return jsonify({"error": "Email and a password of at least 12 characters are required."}), 400
    if role not in {"admin", "inspector"}:
        return jsonify({"error": "Unsupported user role."}), 400
    if User.query.filter_by(email=email.lower().strip()).first():
        return jsonify({"error": "Email is already registered."}), 409
    user = User(email=email.lower().strip(), password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "email": user.email, "role": user.role}), 201
