from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from auth.dependencies import require_role
from db.models import Lesson, TeacherAccessRequest, User
from db.session import get_db


router = APIRouter(prefix="/api/admin", tags=["admin"])


def _request_payload(item: TeacherAccessRequest) -> dict:
    return {
        "id": item.id,
        "status": item.status,
        "user": {"id": item.user.id, "email": item.user.email, "display_name": item.user.display_name, "role": item.user.role},
        "created_at": item.created_at.isoformat(),
    }


@router.get("/teacher-access-requests")
async def list_teacher_requests(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    items = list(db.scalars(
        select(TeacherAccessRequest)
        .options(selectinload(TeacherAccessRequest.user))
        .order_by(TeacherAccessRequest.created_at.desc())
    ))
    return {"requests": [_request_payload(item) for item in items]}


@router.post("/teacher-access-requests/{request_id}/{decision}")
async def review_teacher_request(
    request_id: int, decision: str, admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Decision must be approve or reject")
    item = db.get(TeacherAccessRequest, request_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Teacher request not found")
    item.status = "approved" if decision == "approve" else "rejected"
    item.reviewed_by_user_id = admin.id
    item.reviewed_at = datetime.utcnow()
    if decision == "approve":
        item.user.role = "teacher"
    db.commit()
    return _request_payload(item)


@router.post("/teachers/{user_id}/revoke")
async def revoke_teacher(user_id: str, _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None or user.role != "teacher":
        raise HTTPException(status_code=404, detail="Teacher not found")
    owned_count = db.scalar(select(func.count()).select_from(Lesson).where(Lesson.owner_user_id == user.id)) or 0
    if owned_count:
        raise HTTPException(status_code=409, detail="Teacher owns classes and cannot be revoked")
    user.role = "student"
    db.commit()
    return {"message": "Teacher access revoked"}
