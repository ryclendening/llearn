from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from db.models import (
    Assessment,
    ChatSession,
    CourseMaterial,
    Enrollment,
    ExampleAttempt,
    ExtractedExampleProblem,
    LearningObjective,
    Lesson,
    Message,
    PublishedExample,
    Student,
)


DEFAULT_LESSON = {
    "lesson_id": "science101",
    "title": "Introduction to planets",
    "objectives": [
        "Understand the number of planets in the solar system",
        "Know the largest planet",
        "Know the smallest planet",
        "Demonstrate understanding of an orbit",
    ],
}


def seed_default_lesson(db: Session) -> None:
    if get_lesson(db, DEFAULT_LESSON["lesson_id"]):
        return
    upsert_lesson(
        db,
        lesson_id=DEFAULT_LESSON["lesson_id"],
        title=DEFAULT_LESSON["title"],
        objectives=DEFAULT_LESSON["objectives"],
    )


def get_lesson(db: Session, lesson_id: str) -> Lesson | None:
    return db.scalar(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.objectives))
    )


def list_lessons(db: Session) -> list[Lesson]:
    return list(
        db.scalars(
            select(Lesson)
            .options(selectinload(Lesson.objectives))
            .order_by(Lesson.created_at, Lesson.id)
        )
    )


def delete_lesson(db: Session, lesson_id: str) -> bool:
    lesson = get_lesson(db, lesson_id)
    if lesson is None:
        return False

    db.delete(lesson)
    db.commit()
    return True


def lesson_to_payload(lesson: Lesson) -> dict:
    return {
        "title": lesson.title,
        "objectives": [objective.text for objective in lesson.objectives],
    }


def upsert_lesson(db: Session, *, lesson_id: str, title: str, objectives: list[str]) -> Lesson:
    lesson = get_lesson(db, lesson_id)
    if lesson is None:
        lesson = Lesson(id=lesson_id, title=title)
        db.add(lesson)
        db.flush()
    else:
        lesson.title = title
        lesson.objectives.clear()
        db.flush()

    for index, text in enumerate(objectives, start=1):
        lesson.objectives.append(LearningObjective(text=text, position=index))

    db.commit()
    db.refresh(lesson)
    return lesson


def create_student_enrollment(db: Session, *, student_id: str, lesson_id: str) -> None:
    if not get_lesson(db, lesson_id):
        raise ValueError("lesson_not_found")

    student = db.get(Student, student_id)
    if student is None:
        student = Student(id=student_id)
        db.add(student)
        db.flush()

    enrollment = db.get(Enrollment, {"student_id": student_id, "lesson_id": lesson_id})
    if enrollment is None:
        db.add(Enrollment(student_id=student_id, lesson_id=lesson_id))

    db.commit()


def get_student(db: Session, student_id: str) -> Student | None:
    return db.get(Student, student_id)


def list_student_ids(db: Session) -> list[str]:
    return list(db.scalars(select(Student.id).order_by(Student.created_at, Student.id)))


def get_student_lesson_id(db: Session, student_id: str) -> str | None:
    return db.scalar(
        select(Enrollment.lesson_id)
        .where(Enrollment.student_id == student_id)
        .order_by(Enrollment.created_at.desc())
    )


def get_roster(db: Session, lesson_id: str) -> list[str] | None:
    if not get_lesson(db, lesson_id):
        return None
    return list(
        db.scalars(
            select(Enrollment.student_id)
            .where(Enrollment.lesson_id == lesson_id)
            .order_by(Enrollment.created_at, Enrollment.student_id)
        )
    )


def create_chat_session(db: Session, *, student_id: str, lesson_id: str) -> ChatSession:
    chat_session = ChatSession(student_id=student_id, lesson_id=lesson_id)
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def add_message(db: Session, *, chat_session_id: int, role: str, content: str) -> None:
    db.add(Message(chat_session_id=chat_session_id, role=role, content=content))
    db.commit()


def list_chat_logs(db: Session, *, student_id: str, lesson_id: str) -> list[dict]:
    sessions = list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.student_id == student_id, ChatSession.lesson_id == lesson_id)
            .options(selectinload(ChatSession.messages))
            .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
        )
    )
    logs = [
        {
            "session_id": session.id,
            "created_at": session.created_at.isoformat(),
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }
                for message in sorted(session.messages, key=lambda item: (item.created_at, item.id))
            ],
        }
        for session in sessions
    ]
    practice_attempts = list(
        db.scalars(
            select(ExampleAttempt)
            .where(ExampleAttempt.student_id == student_id, ExampleAttempt.lesson_id == lesson_id)
            .options(selectinload(ExampleAttempt.example))
            .order_by(ExampleAttempt.created_at, ExampleAttempt.id)
        )
    )
    if practice_attempts:
        logs.append({
            "session_id": "example-practice",
            "created_at": practice_attempts[0].created_at.isoformat(),
            "messages": [
                item
                for attempt in practice_attempts
                for item in [
                    {
                        "id": f"attempt-{attempt.id}-answer",
                        "role": "user",
                        "content": f"Example problem:\n{attempt.example.problem_text}\n\nStudent answer:\n{attempt.submitted_answer}",
                        "created_at": attempt.created_at.isoformat(),
                    },
                    {
                        "id": f"attempt-{attempt.id}-judge",
                        "role": "judge",
                        "content": f"{'Correct' if attempt.is_correct else 'Not quite yet'} ({round(attempt.score * 100)}%). {attempt.feedback}",
                        "created_at": attempt.created_at.isoformat(),
                    },
                ]
            ],
        })
    return logs


def delete_chat_session(
    db: Session,
    *,
    session_id: int,
    student_id: str,
    lesson_id: str,
) -> bool:
    chat_session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.student_id == student_id,
            ChatSession.lesson_id == lesson_id,
        )
    )
    if not chat_session:
        return False
    db.delete(chat_session)
    db.commit()
    return True


def save_assessment(
    db: Session,
    *,
    student_id: str,
    lesson_id: str,
    scores: dict,
    mastered: bool,
) -> Assessment:
    assessment = Assessment(
        student_id=student_id,
        lesson_id=lesson_id,
        scores=scores,
        mastered=mastered,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_latest_assessment(db: Session, student_id: str, lesson_id: str | None = None) -> Assessment | None:
    query = select(Assessment).where(Assessment.student_id == student_id)
    if lesson_id:
        query = query.where(Assessment.lesson_id == lesson_id)
    return db.scalar(query.order_by(Assessment.created_at.desc(), Assessment.id.desc()))


def create_course_material(
    db: Session,
    *,
    lesson_id: str,
    filename: str,
    content_type: str | None,
    storage_path: str,
    vector_document_id: str,
) -> CourseMaterial:
    if not get_lesson(db, lesson_id):
        raise ValueError("lesson_not_found")

    material = CourseMaterial(
        lesson_id=lesson_id,
        filename=filename,
        content_type=content_type,
        storage_path=storage_path,
        vector_document_id=vector_document_id,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def update_course_material_ingest_result(
    db: Session,
    *,
    material_id: int,
    status: str,
    chunk_count: int = 0,
    error_message: str | None = None,
) -> CourseMaterial:
    material = db.get(CourseMaterial, material_id)
    if material is None:
        raise ValueError("material_not_found")

    material.status = status
    material.chunk_count = chunk_count
    material.error_message = error_message
    db.commit()
    db.refresh(material)
    return material


def update_course_material_extraction_result(
    db: Session,
    *,
    material_id: int,
    status: str,
    error_message: str | None = None,
) -> CourseMaterial:
    material = db.get(CourseMaterial, material_id)
    if material is None:
        raise ValueError("material_not_found")

    material.extraction_status = status
    material.extraction_error = error_message
    db.commit()
    db.refresh(material)
    return material


def get_course_material(db: Session, material_id: int) -> CourseMaterial | None:
    return db.get(CourseMaterial, material_id)


def delete_course_material(db: Session, material_id: int) -> CourseMaterial | None:
    material = get_course_material(db, material_id)
    if material is None:
        return None

    db.delete(material)
    db.commit()
    return material


def count_course_materials_with_storage_path(db: Session, storage_path: str) -> int:
    return db.scalar(select(func.count()).select_from(CourseMaterial).where(CourseMaterial.storage_path == storage_path)) or 0


def list_course_materials(db: Session, lesson_id: str) -> list[CourseMaterial] | None:
    if not get_lesson(db, lesson_id):
        return None
    return list(
        db.scalars(
            select(CourseMaterial)
            .where(CourseMaterial.lesson_id == lesson_id)
            .order_by(CourseMaterial.created_at.desc(), CourseMaterial.id.desc())
        )
    )


def course_material_to_payload(material: CourseMaterial) -> dict:
    return {
        "id": material.id,
        "class_id": material.lesson_id,
        "filename": material.filename,
        "content_type": material.content_type,
        "vector_document_id": material.vector_document_id,
        "status": material.status,
        "chunk_count": material.chunk_count,
        "error_message": material.error_message,
        "extraction_status": material.extraction_status,
        "extraction_error": material.extraction_error,
        "created_at": material.created_at.isoformat(),
    }


def create_extracted_examples(
    db: Session,
    *,
    material_id: int,
    examples: list[dict],
) -> list[ExtractedExampleProblem]:
    material = get_course_material(db, material_id)
    if material is None:
        raise ValueError("material_not_found")

    created = []
    existing_keys = {
        _example_key(example.problem_text)
        for example in list_material_examples(db, material_id) or []
    }
    for example in examples:
        problem_text = _clean_db_text(example.get("problem_text")).strip()
        solution_text = _clean_db_text(example.get("solution_text")).strip()
        if not problem_text or not solution_text:
            continue
        example_key = _example_key(problem_text)
        if example_key in existing_keys:
            continue
        existing_keys.add(example_key)

        created.append(
            ExtractedExampleProblem(
                material_id=material_id,
                page_start=_optional_int(example.get("page_start")),
                page_end=_optional_int(example.get("page_end")),
                problem_text=problem_text,
                solution_text=solution_text,
                confidence=_bounded_float(example.get("confidence"), default=0.0),
                status="draft",
            )
        )

    db.add_all(created)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    for example in created:
        db.refresh(example)
    return created


def _clean_db_text(value: object) -> str:
    # PostgreSQL text fields reject NUL bytes, which can appear in PDF extraction output.
    return str(value or "").replace("\x00", "")


def list_material_examples(db: Session, material_id: int) -> list[ExtractedExampleProblem] | None:
    if get_course_material(db, material_id) is None:
        return None
    return list(
        db.scalars(
            select(ExtractedExampleProblem)
            .where(ExtractedExampleProblem.material_id == material_id)
            .order_by(ExtractedExampleProblem.page_start, ExtractedExampleProblem.id)
        )
    )


def get_example(db: Session, example_id: int) -> ExtractedExampleProblem | None:
    return db.get(ExtractedExampleProblem, example_id)


def publish_examples_for_class(db: Session, *, lesson_id: str, example_ids: list[int]) -> list[PublishedExample]:
    if not get_lesson(db, lesson_id):
        raise ValueError("lesson_not_found")

    published = []
    next_position = db.scalar(
        select(func.coalesce(func.max(PublishedExample.position), 0))
        .where(PublishedExample.lesson_id == lesson_id)
    ) or 0

    for example_id in example_ids:
        example = get_example(db, example_id)
        if example is None:
            raise ValueError("example_not_found")
        if example.material.lesson_id != lesson_id:
            raise ValueError("example_not_found")

        existing = db.scalar(
            select(PublishedExample)
            .where(PublishedExample.lesson_id == lesson_id, PublishedExample.example_id == example_id)
        )
        if existing:
            existing.enabled = True
            published.append(existing)
            continue

        next_position += 1
        item = PublishedExample(
            lesson_id=lesson_id,
            example_id=example_id,
            enabled=True,
            position=next_position,
        )
        db.add(item)
        published.append(item)

    db.commit()
    for item in published:
        db.refresh(item)
    return published


def list_published_examples(db: Session, lesson_id: str, *, include_disabled: bool = False) -> list[PublishedExample] | None:
    if not get_lesson(db, lesson_id):
        return None
    query = (
        select(PublishedExample)
        .where(PublishedExample.lesson_id == lesson_id)
        .options(selectinload(PublishedExample.example).selectinload(ExtractedExampleProblem.material))
        .order_by(PublishedExample.position, PublishedExample.id)
    )
    if not include_disabled:
        query = query.where(PublishedExample.enabled == True)  # noqa: E712
    return list(db.scalars(query))


def unpublish_example_for_class(db: Session, *, lesson_id: str, example_id: int) -> bool:
    item = db.scalar(
        select(PublishedExample)
        .where(PublishedExample.lesson_id == lesson_id, PublishedExample.example_id == example_id)
    )
    if item is None:
        return False

    db.delete(item)
    db.commit()
    return True


def is_example_published_for_class(db: Session, *, lesson_id: str, example_id: int) -> bool:
    return db.scalar(
        select(func.count())
        .select_from(PublishedExample)
        .where(
            PublishedExample.lesson_id == lesson_id,
            PublishedExample.example_id == example_id,
            PublishedExample.enabled == True,  # noqa: E712
        )
    ) > 0


def save_example_attempt(
    db: Session,
    *,
    student_id: str,
    lesson_id: str,
    example_id: int,
    submitted_answer: str,
    judgment: dict,
) -> ExampleAttempt:
    attempt = ExampleAttempt(
        student_id=student_id,
        lesson_id=lesson_id,
        example_id=example_id,
        submitted_answer=submitted_answer,
        judgment=judgment,
        is_correct=bool(judgment.get("is_correct")),
        score=_bounded_float(judgment.get("score"), default=0.0),
        feedback=str(judgment.get("feedback") or "").strip() or "Your answer was reviewed.",
        reasoning_summary=str(judgment.get("reasoning_summary") or "").strip() or None,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def list_example_attempts(
    db: Session,
    *,
    student_id: str,
    lesson_id: str,
    example_id: int | None = None,
) -> list[ExampleAttempt]:
    query = select(ExampleAttempt).where(ExampleAttempt.student_id == student_id, ExampleAttempt.lesson_id == lesson_id)
    if example_id is not None:
        query = query.where(ExampleAttempt.example_id == example_id)
    return list(db.scalars(query.order_by(ExampleAttempt.created_at.desc(), ExampleAttempt.id.desc())))


def get_example_performance(db: Session, *, student_id: str, lesson_id: str) -> dict:
    published = list_published_examples(db, lesson_id) or []
    attempts = list_example_attempts(db, student_id=student_id, lesson_id=lesson_id)
    attempts_by_example: dict[int, list[ExampleAttempt]] = {}
    for attempt in attempts:
        attempts_by_example.setdefault(attempt.example_id, []).append(attempt)

    details = []
    correct_count = 0
    attempted_count = 0
    for item in published:
        example_attempts = attempts_by_example.get(item.example_id, [])
        best_attempt = _best_attempt(example_attempts)
        latest_attempt = example_attempts[0] if example_attempts else None
        is_correct = bool(best_attempt and best_attempt.is_correct)
        if example_attempts:
            attempted_count += 1
        if is_correct:
            correct_count += 1

        details.append({
            "example_id": item.example_id,
            "title": _example_title(item.example.problem_text),
            "attempted": bool(example_attempts),
            "correct": is_correct,
            "best_score": best_attempt.score if best_attempt else 0,
            "latest_feedback": latest_attempt.feedback if latest_attempt else None,
        })

    return {
        "assigned_count": len(published),
        "attempted_count": attempted_count,
        "correct_count": correct_count,
        "examples": details,
    }


def example_to_payload(example: ExtractedExampleProblem, *, include_solution: bool = True) -> dict:
    payload = {
        "id": example.id,
        "material_id": example.material_id,
        "filename": example.material.filename if example.material else None,
        "page_start": example.page_start,
        "page_end": example.page_end,
        "problem_text": example.problem_text,
        "confidence": example.confidence,
        "status": example.status,
        "created_at": example.created_at.isoformat(),
    }
    if include_solution:
        payload["solution_text"] = example.solution_text
    return payload


def published_example_to_payload(item: PublishedExample, *, include_solution: bool = False) -> dict:
    payload = example_to_payload(item.example, include_solution=include_solution)
    payload.update({
        "published_id": item.id,
        "class_id": item.lesson_id,
        "position": item.position,
        "enabled": item.enabled,
    })
    return payload


def attempt_to_payload(attempt: ExampleAttempt) -> dict:
    return {
        "id": attempt.id,
        "student_id": attempt.student_id,
        "class_id": attempt.lesson_id,
        "example_id": attempt.example_id,
        "submitted_answer": attempt.submitted_answer,
        "is_correct": attempt.is_correct,
        "score": attempt.score,
        "feedback": attempt.feedback,
        "reasoning_summary": attempt.reasoning_summary,
        "created_at": attempt.created_at.isoformat(),
    }


def _optional_int(value) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _bounded_float(value, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))


def _best_attempt(attempts: list[ExampleAttempt]) -> ExampleAttempt | None:
    if not attempts:
        return None
    correct_attempts = [attempt for attempt in attempts if attempt.is_correct]
    if correct_attempts:
        return max(correct_attempts, key=lambda attempt: (attempt.score, attempt.created_at, attempt.id))
    return max(attempts, key=lambda attempt: (attempt.score, attempt.created_at, attempt.id))


def _example_title(problem_text: str) -> str:
    first_line = " ".join(problem_text.strip().split())
    return first_line[:80] + ("..." if len(first_line) > 80 else "")


def _example_key(problem_text: str) -> str:
    return "".join(character for character in problem_text.lower() if character.isalnum())[:180]
