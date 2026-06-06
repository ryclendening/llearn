from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.dependencies import require_role
from db.crud import delete_chat_session, get_example_performance, get_latest_assessment, get_lesson, get_student, list_chat_logs
from db.models import User
from db.session import get_db


router = APIRouter(prefix="/api", tags=["performance"])


def _performance_payload(db: Session, *, user_id: str, class_id: str | None) -> dict:
    """Returns the most recent persisted assessment for a student."""
    if not get_student(db, user_id):
        raise HTTPException(status_code=404, detail="Student not found")

    assessment = get_latest_assessment(db, user_id, lesson_id=class_id)
    example_performance = get_example_performance(db, student_id=user_id, lesson_id=class_id) if class_id else None
    if not assessment:
        payload = {"message": "No assessments found for student."}
        if example_performance is not None:
            payload["example_performance"] = example_performance
        return payload

    payload = {
        "student_id": user_id,
        "assessment": assessment.scores,
        "mastered": assessment.mastered,
    }
    if example_performance is not None:
        payload["example_performance"] = example_performance
    return payload


@router.get("/performance/{user_id}")
async def get_performance(
    user_id: str, class_id: str | None = Query(default=None),
    user: User = Depends(require_role("teacher", "student")), db: Session = Depends(get_db),
):
    if user.role == "student" and user.id != user_id:
        raise HTTPException(status_code=403, detail="Students may view only their own performance")
    if user.role == "teacher":
        lesson = get_lesson(db, class_id) if class_id else None
        if lesson is None or lesson.owner_user_id != user.id:
            raise HTTPException(status_code=403, detail="You do not own this class")
    return _performance_payload(db, user_id=user_id, class_id=class_id)


@router.get("/me/performance")
async def get_my_performance(
    class_id: str = Query(...),
    student: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    if student.student is None or not any(item.lesson_id == class_id for item in student.student.enrollments):
        raise HTTPException(status_code=403, detail="Student is not enrolled in this class")
    return _performance_payload(db, user_id=student.id, class_id=class_id)


@router.get("/classes/{class_id}/students/{user_id}/chat-logs")
async def get_student_chat_logs(
    class_id: str, user_id: str, teacher: User = Depends(require_role("teacher")), db: Session = Depends(get_db),
):
    lesson = get_lesson(db, class_id)
    if lesson and lesson.owner_user_id != teacher.id:
        raise HTTPException(status_code=403, detail="You do not own this class")
    if not get_student(db, user_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return {"sessions": list_chat_logs(db, student_id=user_id, lesson_id=class_id)}


@router.delete("/classes/{class_id}/students/{user_id}/chat-sessions/{session_id}")
async def delete_student_chat_session(
    class_id: str, user_id: str, session_id: int,
    teacher: User = Depends(require_role("teacher")), db: Session = Depends(get_db),
):
    lesson = get_lesson(db, class_id)
    if lesson and lesson.owner_user_id != teacher.id:
        raise HTTPException(status_code=403, detail="You do not own this class")
    if not get_student(db, user_id):
        raise HTTPException(status_code=404, detail="Student not found")
    deleted = delete_chat_session(db, session_id=session_id, student_id=user_id, lesson_id=class_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"message": "Chat session deleted"}
