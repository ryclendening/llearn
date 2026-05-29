from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import random_lesson_gen
from db.crud import (
    count_course_materials_with_storage_path,
    delete_lesson,
    lesson_to_payload,
    list_course_materials,
    list_lessons,
    upsert_lesson,
)
from db.session import get_db
from vector_db.vector_store import get_vector_db


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


@router.delete("/learning-objectives/{lesson_id}")
async def remove_learning_objectives(lesson_id: str, db: Session = Depends(get_db)):
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
