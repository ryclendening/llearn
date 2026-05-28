from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from db.models import Assessment, ChatSession, Enrollment, LearningObjective, Lesson, Message, Student


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


def get_latest_assessment(db: Session, student_id: str) -> Assessment | None:
    return db.scalar(
        select(Assessment)
        .where(Assessment.student_id == student_id)
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
    )
