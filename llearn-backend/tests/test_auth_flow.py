from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

from db.session import Base, get_db
import db.models  # noqa: F401
from routers.admin import router as admin_router
from routers.auth import router


class AuthFlowTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        session_local = sessionmaker(bind=engine)
        app = FastAPI()
        app.add_middleware(SessionMiddleware, secret_key="test-secret")
        app.include_router(router)
        app.include_router(admin_router)

        def test_db():
            db = session_local()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def test_dev_login_creates_student_session_and_me_uses_cookie(self):
        with patch("routers.auth.AUTH_DEV_BYPASS", True), patch("routers.auth.APP_ENV", "development"):
            response = self.client.post("/api/auth/dev-login", json={"email": "student@example.com"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "student")
        self.assertIn("llearn_session", response.cookies)
        self.assertEqual(self.client.get("/api/auth/me").json()["email"], "student@example.com")

    def test_dev_login_is_hidden_when_disabled(self):
        with patch("routers.auth.AUTH_DEV_BYPASS", False):
            response = self.client.post("/api/auth/dev-login", json={"email": "student@example.com"})
        self.assertEqual(response.status_code, 404)

    def test_dev_login_can_act_as_teacher(self):
        with patch("routers.auth.AUTH_DEV_BYPASS", True), patch("routers.auth.APP_ENV", "development"):
            response = self.client.post(
                "/api/auth/dev-login",
                json={"email": "developer@example.com", "role": "teacher"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "teacher")

    def test_dev_admin_login_requires_allowlisted_email(self):
        with (
            patch("routers.auth.AUTH_DEV_BYPASS", True),
            patch("routers.auth.APP_ENV", "development"),
            patch("routers.auth.ADMIN_EMAILS", {"admin@example.com"}),
        ):
            denied = self.client.post(
                "/api/auth/dev-login",
                json={"email": "developer@example.com", "role": "admin"},
            )
            allowed = self.client.post(
                "/api/auth/dev-login",
                json={"email": "admin@example.com", "role": "admin"},
            )
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(allowed.json()["role"], "admin")

    def test_me_rejects_missing_session(self):
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_admin_can_approve_pending_teacher_request(self):
        with (
            patch("routers.auth.AUTH_DEV_BYPASS", True),
            patch("routers.auth.APP_ENV", "development"),
            patch("routers.auth.AUTH_DEV_AUTO_APPROVE_TEACHERS", False),
        ):
            self.client.post("/api/auth/dev-login", json={"email": "teacher@example.com"})
            request = self.client.post("/api/teacher-access-requests")
            self.assertEqual(request.json()["status"], "pending")

            self.client.cookies.clear()
            with (
                patch("auth.service.ADMIN_EMAILS", {"admin@example.com"}),
                patch("routers.auth.ADMIN_EMAILS", {"admin@example.com"}),
            ):
                self.client.post(
                    "/api/auth/dev-login",
                    json={"email": "admin@example.com", "role": "admin"},
                )

            items = self.client.get("/api/admin/teacher-access-requests").json()["requests"]
            response = self.client.post(f"/api/admin/teacher-access-requests/{items[0]['id']}/approve")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["role"], "teacher")


if __name__ == "__main__":
    unittest.main()
