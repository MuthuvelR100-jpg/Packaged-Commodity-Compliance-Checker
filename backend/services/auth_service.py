from functools import wraps

from flask import jsonify, session
from werkzeug.security import check_password_hash

from models.user import User


def current_user():
    user_id = session.get("user_id")
    return User.query.get(user_id) if user_id else None


def login_required(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "Authentication required."}), 401
        return handler(*args, **kwargs)
    return wrapped


def admin_required(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify({"error": "Authentication required."}), 401
        if user.role != "admin":
            return jsonify({"error": "Administrator access required."}), 403
        return handler(*args, **kwargs)
    return wrapped


def authenticate(email: str, password: str):
    user = User.query.filter_by(email=email.lower().strip()).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return None
    return user
