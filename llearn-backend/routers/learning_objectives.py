from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import random_lesson_gen
from auth.dependencies import require_role
from db.crud import (
    count_course_materials_with_storage_path,
    delete_lesson,
    get_lesson,
    lesson_to_payload,
    list_course_materials,
    list_lessons,
    upsert_lesson,
)
from db.session import get_db
from db.models import User
from vector_db.vector_store import get_vector_db


router = APIRouter(prefix="/api", tags=["learning-objectives"])


@router.get("/generate-objectives")
async def generate_objectives(age: int, genre: str, _: User = Depends(require_role("teacher"))):
    return random_lesson_gen.run_graph(age, genre)


@router.post("/learning-objectives")
async def add_learning_objectives(
    request: Request,
    teacher: User = Depends(require_role("teacher")),
    db: Session = Depends(get_db),
):
    data = await request.json()
    for field in ["lesson_id", "title", "objectives"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")
    if not isinstance(data["objectives"], list) or not all(isinstance(o, str) for o in data["objectives"]):
        raise HTTPException(status_code=400, detail="'objectives' must be a list of strings")

    try:
        upsert_lesson(
            db, lesson_id=data["lesson_id"], title=data["title"],
            objectives=data["objectives"], owner_user_id=teacher.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="You do not own this class") from exc
    return {"message": f"Learning objectives for '{data['lesson_id']}' received", "count": len(data["objectives"])}


@router.get("/learning-objectives")
async def get_learning_objectives(user: User = Depends(require_role("teacher", "student")), db: Session = Depends(get_db)):
    lessons = list_lessons(db, owner_user_id=user.id) if user.role == "teacher" else list_lessons(db, student_id=user.id)
    return {lesson.id: lesson_to_payload(lesson) for lesson in lessons}


@router.delete("/learning-objectives/{lesson_id}")
async def remove_learning_objectives(
    lesson_id: str,
    teacher: User = Depends(require_role("teacher")),
    db: Session = Depends(get_db),
):
    lesson = get_lesson(db, lesson_id)
    if lesson and lesson.owner_user_id != teacher.id:
        raise HTTPException(status_code=403, detail="You do not own this class")
    materials = list_course_materials(db, lesson_id)
    if materials is None:
        raise HTTPException(status_code=404, detail=f"Class session '{lesson_id}' not found")

    materials_with_chunks = [material for material in materials if material.chunk_count > 0]
    if materials_with_chunks:
        vector_db = get_vector_db()
        try:
            for material in materials_with_chunks:
                vector_db.delete_by_material_id(material.id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Failed to delete class material chunks from the vector store.") from exc
        finally:
            vector_db.close()

    storage_paths = {material.storage_path for material in materials}
    if not delete_lesson(db, lesson_id):
        raise HTTPException(status_code=404, detail=f"Class session '{lesson_id}' not found")

    for storage_path in storage_paths:
        if count_course_materials_with_storage_path(db, storage_path) == 0:
            Path(storage_path).unlink(missing_ok=True)

    return {"message": f"Class session '{lesson_id}' deleted"}
