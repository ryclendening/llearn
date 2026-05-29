from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.crud import get_example_performance, get_latest_assessment, get_student, list_chat_logs
from db.session import get_db


router = APIRouter(prefix="/api", tags=["performance"])


@router.get("/performance/{user_id}")
async def get_performance(user_id: str, class_id: str | None = Query(default=None), db: Session = Depends(get_db)):
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


@router.get("/classes/{class_id}/students/{user_id}/chat-logs")
async def get_student_chat_logs(class_id: str, user_id: str, db: Session = Depends(get_db)):
    if not get_student(db, user_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return {"sessions": list_chat_logs(db, student_id=user_id, lesson_id=class_id)}
