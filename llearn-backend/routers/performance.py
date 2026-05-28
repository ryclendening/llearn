from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.crud import get_latest_assessment, get_student
from db.session import get_db


router = APIRouter(prefix="/api", tags=["performance"])


@router.get("/performance/{user_id}")
async def get_performance(user_id: str, db: Session = Depends(get_db)):
    """Returns the most recent persisted assessment for a student."""
    if not get_student(db, user_id):
        raise HTTPException(status_code=404, detail="Student not found")

    assessment = get_latest_assessment(db, user_id)
    if not assessment:
        return {"message": "No assessments found for student."}

    return {
        "student_id": user_id,
        "assessment": assessment.scores,
        "mastered": assessment.mastered,
    }
