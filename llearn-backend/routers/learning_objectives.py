from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import random_lesson_gen
from db.crud import lesson_to_payload, list_lessons, upsert_lesson
from db.session import get_db


router = APIRouter(prefix="/api", tags=["learning-objectives"])


@router.get("/generate-objectives")
async def generate_objectives(age: int, genre: str):
    return random_lesson_gen.run_graph(age, genre)


@router.post("/learning-objectives")
async def add_learning_objectives(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    for field in ["lesson_id", "title", "objectives"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")
    if not isinstance(data["objectives"], list) or not all(isinstance(o, str) for o in data["objectives"]):
        raise HTTPException(status_code=400, detail="'objectives' must be a list of strings")

    upsert_lesson(
        db,
        lesson_id=data["lesson_id"],
        title=data["title"],
        objectives=data["objectives"],
    )
    return {"message": f"Learning objectives for '{data['lesson_id']}' received", "count": len(data["objectives"])}


@router.get("/learning-objectives")
async def get_learning_objectives(db: Session = Depends(get_db)):
    return {lesson.id: lesson_to_payload(lesson) for lesson in list_lessons(db)}
