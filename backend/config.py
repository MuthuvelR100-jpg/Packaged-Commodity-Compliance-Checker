import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(PROJECT_DIR / ".env")


class Config:
    API_PREFIX = "/api"
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    PORT = int(os.getenv("PORT", "5000"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(PROJECT_DIR / "uploads"))
    REPORT_FOLDER = os.getenv("REPORT_FOLDER", str(PROJECT_DIR / "reports"))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{str(PROJECT_DIR / 'backend' / 'database' / 'app.db').replace(chr(92), '/')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173,http://10.152.75.201:5173").split(",")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
