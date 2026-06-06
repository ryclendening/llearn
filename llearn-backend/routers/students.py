from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.dependencies import require_role
from db.crud import get_lesson
from db.crud import create_student_enrollment, get_roster
from db.models import User
from db.session import get_db


router = APIRouter(prefix="/api", tags=["students"])


class JoinClassRequest(BaseModel):
    class_id: str


@router.post("/classes/join")
async def join_class(
    request: JoinClassRequest,
    student: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    try:
        create_student_enrollment(db, student_id=student.id, lesson_id=request.class_id.strip())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Joined class", "class_id": request.class_id.strip()}


@router.get("/get-roster/{lesson_id}")
async def get_lesson_roster(
    lesson_id: str,
    teacher: User = Depends(require_role("teacher")),
    db: Session = Depends(get_db),
):
    lesson = get_lesson(db, lesson_id)
    if lesson and lesson.owner_user_id != teacher.id:
        raise HTTPException(status_code=403, detail="You do not own this class")
    roster = get_roster(db, lesson_id)
    if roster is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"roster": roster}
