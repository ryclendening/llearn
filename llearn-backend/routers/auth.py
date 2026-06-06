from __future__ import annotations

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Literal

from auth.config import (
    ADMIN_EMAILS, APP_ENV, AUTH_COOKIE_NAME, AUTH_COOKIE_SECURE, AUTH_DEV_AUTO_APPROVE_TEACHERS,
    AUTH_DEV_BYPASS, FRONTEND_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
)
from auth.dependencies import current_user, user_payload
from auth.service import (
    create_auth_session, request_teacher_access, revoke_auth_session,
    teacher_request_status, upsert_oauth_user,
)
from db.models import Student, User
from db.session import get_db


router = APIRouter(prefix="/api", tags=["auth"])
oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


class DevLoginRequest(BaseModel):
    email: str
    display_name: str | None = None
    role: Literal["student", "teacher", "admin"] = "student"


def _set_session_cookie(response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE_NAME, token, max_age=7 * 24 * 60 * 60, httponly=True,
        secure=AUTH_COOKIE_SECURE, samesite="lax", path="/",
    )


@router.get("/auth/login")
async def login(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    return await oauth.google.authorize_redirect(request, str(request.url_for("auth_callback")))


@router.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    info = token.get("userinfo") or await oauth.google.userinfo(token=token)
    if not info.get("email") or not info.get("email_verified", True):
        raise HTTPException(status_code=403, detail="A verified Google email is required")
    user = upsert_oauth_user(
        db, email=info["email"], display_name=info.get("name") or info["email"],
        google_subject=info.get("sub"),
    )
    response = RedirectResponse(FRONTEND_URL)
    _set_session_cookie(response, create_auth_session(db, user))
    return response


@router.post("/auth/dev-login")
async def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)):
    if not AUTH_DEV_BYPASS or APP_ENV == "production":
        raise HTTPException(status_code=404, detail="Not found")
    if payload.role == "admin" and payload.email.strip().lower() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin development login requires an email in ADMIN_EMAILS")
    user = upsert_oauth_user(
        db, email=payload.email, display_name=payload.display_name or payload.email,
        google_subject=None,
    )
    user.role = payload.role
    if payload.role == "student" and user.student is None:
        db.add(Student(id=user.id, user_id=user.id))
    db.commit()
    db.refresh(user)
    response = JSONResponse(user_payload(user, teacher_request_status(db, user.id)))
    _set_session_cookie(response, create_auth_session(db, user))
    return response


@router.get("/auth/me")
async def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_payload(user, teacher_request_status(db, user.id))


@router.post("/auth/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    revoke_auth_session(db, request.cookies.get(AUTH_COOKIE_NAME))
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return response


@router.post("/teacher-access-requests")
async def create_teacher_request(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=409, detail="Only students may request teacher access")
    item = request_teacher_access(
        db, user, auto_approve=AUTH_DEV_AUTO_APPROVE_TEACHERS and APP_ENV != "production",
    )
    return {"status": item.status}
