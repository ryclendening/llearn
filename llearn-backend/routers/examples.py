from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.crud import (
    attempt_to_payload,
    create_extracted_examples,
    example_to_payload,
    get_example,
    get_example_performance,
    get_course_material,
    get_student,
    is_example_published_for_class,
    list_example_attempts,
    list_material_examples,
    list_published_examples,
    publish_examples_for_class,
    published_example_to_payload,
    save_example_attempt,
    unpublish_example_for_class,
)
from db.session import get_db
from example_ai import extract_example_problems, grade_example_attempt


router = APIRouter(prefix="/api", tags=["examples"])


class PublishExamplesRequest(BaseModel):
    example_ids: list[int]


class SubmitAttemptRequest(BaseModel):
    user_id: str
    answer: str


@router.get("/materials/{material_id}/examples")
async def get_material_examples(material_id: int, db: Session = Depends(get_db)):
    examples = list_material_examples(db, material_id)
    if examples is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"examples": [example_to_payload(example) for example in examples]}


@router.post("/materials/{material_id}/examples/extract")
async def extract_material_examples(material_id: int, db: Session = Depends(get_db)):
    material = get_course_material(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")

    try:
        extracted = extract_example_problems(material.storage_path)
        created = create_extracted_examples(db, material_id=material_id, examples=extracted)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Example extraction failed.") from exc

    examples = list_material_examples(db, material_id) or []
    return {
        "created_count": len(created),
        "examples": [example_to_payload(example) for example in examples],
    }


@router.post("/classes/{class_id}/examples")
async def publish_class_examples(
    class_id: str,
    request: PublishExamplesRequest,
    db: Session = Depends(get_db),
):
    example_ids = []
    for example_id in request.example_ids:
        if example_id not in example_ids:
            example_ids.append(example_id)
    if not example_ids:
        raise HTTPException(status_code=400, detail="Select at least one example.")

    try:
        published = publish_examples_for_class(db, lesson_id=class_id, example_ids=example_ids)
    except ValueError as exc:
        detail = "Class not found" if str(exc) == "lesson_not_found" else "Example not found"
        raise HTTPException(status_code=404, detail=detail) from exc

    return {"examples": [published_example_to_payload(item, include_solution=True) for item in published]}


@router.get("/classes/{class_id}/examples")
async def get_class_examples(class_id: str, db: Session = Depends(get_db)):
    examples = list_published_examples(db, class_id)
    if examples is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"examples": [published_example_to_payload(item, include_solution=True) for item in examples]}


@router.delete("/classes/{class_id}/examples/{example_id}")
async def unpublish_class_example(class_id: str, example_id: int, db: Session = Depends(get_db)):
    if not unpublish_example_for_class(db, lesson_id=class_id, example_id=example_id):
        raise HTTPException(status_code=404, detail="Published example not found")
    return {"message": "Example unpublished"}


@router.get("/classes/{class_id}/practice-examples")
async def get_practice_examples(class_id: str, db: Session = Depends(get_db)):
    examples = list_published_examples(db, class_id)
    if examples is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"examples": [published_example_to_payload(item, include_solution=False) for item in examples]}


@router.post("/classes/{class_id}/practice-examples/{example_id}/attempts")
async def submit_practice_attempt(
    class_id: str,
    example_id: int,
    request: SubmitAttemptRequest,
    db: Session = Depends(get_db),
):
    answer = request.answer.strip()
    if not answer:
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")
    if not get_student(db, request.user_id):
        raise HTTPException(status_code=404, detail="Student not found")
    if not is_example_published_for_class(db, lesson_id=class_id, example_id=example_id):
        raise HTTPException(status_code=404, detail="Example not found for this class")

    example = get_example(db, example_id)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")

    try:
        judgment = grade_example_attempt(
            problem_text=example.problem_text,
            solution_text=example.solution_text,
            submitted_answer=answer,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to grade example attempt.") from exc

    attempt = save_example_attempt(
        db,
        student_id=request.user_id,
        lesson_id=class_id,
        example_id=example_id,
        submitted_answer=answer,
        judgment=judgment,
    )
    return {"attempt": attempt_to_payload(attempt), "performance": get_example_performance(db, student_id=request.user_id, lesson_id=class_id)}


@router.get("/classes/{class_id}/practice-examples/{example_id}/solution")
async def get_practice_solution(
    class_id: str,
    example_id: int,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    if not is_example_published_for_class(db, lesson_id=class_id, example_id=example_id):
        raise HTTPException(status_code=404, detail="Example not found for this class")

    attempts = list_example_attempts(db, student_id=user_id, lesson_id=class_id, example_id=example_id)
    if not any(not attempt.is_correct for attempt in attempts):
        raise HTTPException(status_code=403, detail="Solution is available after an incorrect attempt.")

    example = get_example(db, example_id)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    return {"example_id": example_id, "solution_text": example.solution_text}
