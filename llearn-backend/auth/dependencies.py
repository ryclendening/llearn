from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from auth.config import AUTH_COOKIE_NAME
from auth.service import get_user_for_session
from db.crud import get_lesson
from db.models import User
from db.session import get_db


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_user_for_session(db, request.cookies.get(AUTH_COOKIE_NAME))
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_role(*roles: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


def require_teacher_owner(class_id: str, user: User = Depends(require_role("teacher")), db: Session = Depends(get_db)) -> User:
    lesson = get_lesson(db, class_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if lesson.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not own this class")
    return user


def require_student_enrollment(class_id: str, user: User = Depends(require_role("student")), db: Session = Depends(get_db)) -> User:
    if user.student is None or not any(enrollment.lesson_id == class_id for enrollment in user.student.enrollments):
        raise HTTPException(status_code=403, detail="Student is not enrolled in this class")
    return user


def user_payload(user: User, teacher_request=None) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "teacher_request_status": teacher_request.status if teacher_request else None,
    }
