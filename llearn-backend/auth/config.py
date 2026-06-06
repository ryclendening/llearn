from __future__ import annotations

import os


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


APP_ENV = os.getenv("APP_ENV", "development").lower()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
AUTH_STATE_SECRET = os.getenv("AUTH_STATE_SECRET", "development-only-change-me")
AUTH_COOKIE_NAME = "llearn_session"
AUTH_COOKIE_SECURE = _flag("AUTH_COOKIE_SECURE", APP_ENV == "production")
AUTH_DEV_BYPASS = _flag("AUTH_DEV_BYPASS")
AUTH_DEV_AUTO_APPROVE_TEACHERS = _flag("AUTH_DEV_AUTO_APPROVE_TEACHERS")
ADMIN_EMAILS = {email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()}
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


def validate_auth_config() -> None:
    if APP_ENV == "production" and (AUTH_DEV_BYPASS or AUTH_DEV_AUTO_APPROVE_TEACHERS):
        raise RuntimeError("Development authentication features cannot be enabled in production.")
    if APP_ENV == "production" and AUTH_STATE_SECRET == "development-only-change-me":
        raise RuntimeError("AUTH_STATE_SECRET must be configured in production.")
