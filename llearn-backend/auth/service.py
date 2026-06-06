from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.config import ADMIN_EMAILS
from db.models import AuthSession, Student, TeacherAccessRequest, User


SESSION_TTL = timedelta(days=7)


def upsert_oauth_user(db: Session, *, email: str, display_name: str, google_subject: str | None) -> User:
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    role = "admin" if normalized_email in ADMIN_EMAILS else None
    if user is None:
        user = User(
            email=normalized_email,
            display_name=display_name.strip() or normalized_email,
            google_subject=google_subject,
            role=role or "student",
        )
        db.add(user)
        db.flush()
    else:
        user.display_name = display_name.strip() or user.display_name
        user.google_subject = google_subject or user.google_subject
        if role:
            user.role = role
    if user.role == "student" and user.student is None:
        db.add(Student(id=user.id, user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


def create_auth_session(db: Session, user: User) -> str:
    for existing in list(db.scalars(select(AuthSession).where(AuthSession.user_id == user.id))):
        db.delete(existing)
    raw_token = secrets.token_urlsafe(48)
    db.add(AuthSession(
        user_id=user.id,
        token_hash=_token_hash(raw_token),
        expires_at=datetime.utcnow() + SESSION_TTL,
    ))
    db.commit()
    return raw_token


def get_user_for_session(db: Session, raw_token: str | None) -> User | None:
    if not raw_token:
        return None
    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _token_hash(raw_token),
            AuthSession.expires_at > datetime.utcnow(),
        )
    )
    return auth_session.user if auth_session else None


def revoke_auth_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    auth_session = db.scalar(select(AuthSession).where(AuthSession.token_hash == _token_hash(raw_token)))
    if auth_session:
        db.delete(auth_session)
        db.commit()


def request_teacher_access(db: Session, user: User, *, auto_approve: bool) -> TeacherAccessRequest:
    existing = db.scalar(
        select(TeacherAccessRequest)
        .where(TeacherAccessRequest.user_id == user.id)
        .order_by(TeacherAccessRequest.created_at.desc(), TeacherAccessRequest.id.desc())
    )
    if existing and existing.status == "pending":
        request = existing
    else:
        request = TeacherAccessRequest(user_id=user.id)
        db.add(request)
    if auto_approve:
        request.status = "approved"
        request.reviewed_at = datetime.utcnow()
        user.role = "teacher"
    db.commit()
    db.refresh(request)
    return request


def teacher_request_status(db: Session, user_id: str) -> TeacherAccessRequest | None:
    return db.scalar(
        select(TeacherAccessRequest)
        .where(TeacherAccessRequest.user_id == user_id)
        .order_by(TeacherAccessRequest.created_at.desc(), TeacherAccessRequest.id.desc())
    )


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
