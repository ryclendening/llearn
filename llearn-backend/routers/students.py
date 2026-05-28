from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.crud import create_student_enrollment, get_roster, list_student_ids
from db.session import get_db


router = APIRouter(prefix="/api", tags=["students"])


@router.post("/create-student")
async def create_student(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    for field in ["user_id", "lesson_id"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")
    try:
        create_student_enrollment(db, student_id=data["user_id"], lesson_id=data["lesson_id"])
    except ValueError:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": f"Student {data['user_id']} created"}


@router.get("/get-students")
async def get_students(db: Session = Depends(get_db)):
    return {"students": list_student_ids(db)}


@router.get("/get-roster/{lesson_id}")
async def get_lesson_roster(lesson_id: str, db: Session = Depends(get_db)):
    roster = get_roster(db, lesson_id)
    if roster is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"roster": roster}
