from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy.pool import StaticPool

from auth.dependencies import current_user
from db.models import CourseMaterial, Enrollment, Lesson, Student, User
from db.session import Base, get_db
import db.models  # noqa: F401
from routers.materials import router as materials_router


class MaterialsAccessTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.session_local = sessionmaker(bind=engine)
        app = FastAPI()
        app.include_router(materials_router)

        def test_db():
            db = self.session_local()
            try:
                yield db
            finally:
                db.close()

        self.current_user = None

        def test_current_user():
            return self.current_user

        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[current_user] = test_current_user
        self.client = TestClient(app)
        self._seed_data()

    def _seed_data(self):
        db = self.session_local()
        try:
            teacher = User(id="teacher-1", email="teacher@example.com", display_name="Teacher", role="teacher")
            student_user = User(id="student-user-1", email="student@example.com", display_name="Student", role="student")
            other_student_user = User(
                id="student-user-2",
                email="other-student@example.com",
                display_name="Other Student",
                role="student",
            )
            student = Student(id="student-1", user=student_user)
            other_student = Student(id="student-2", user=other_student_user)
            lesson = Lesson(id="class-1", title="Fractions", owner_user_id="teacher-1")
            db.add_all([teacher, student_user, other_student_user, student, other_student, lesson])
            db.flush()
            db.add(Enrollment(student_id="student-1", lesson_id="class-1"))
            db.add(
                CourseMaterial(
                    lesson_id="class-1",
                    filename="fractions-notes.pdf",
                    content_type="application/pdf",
                    storage_path="/tmp/fractions-notes.pdf",
                    vector_document_id="class-1:doc-1",
                    status="ready",
                    chunk_count=4,
                    error_message="teacher-only detail",
                    extraction_status="completed",
                    extraction_error="teacher-only extraction detail",
                )
            )
            db.add(
                CourseMaterial(
                    lesson_id="class-1",
                    filename="practice-review.pdf",
                    content_type="application/pdf",
                    storage_path="/tmp/practice-review.pdf",
                    vector_document_id="class-1:doc-2",
                    status="ready",
                    chunk_count=2,
                    extraction_status="completed",
                )
            )
            db.commit()
        finally:
            db.close()

    def _user(self, user_id: str) -> User:
        db = self.session_local()
        try:
            return db.scalar(
                select(User)
                .where(User.id == user_id)
                .options(selectinload(User.student).selectinload(Student.enrollments))
            )
        finally:
            db.close()

    def test_enrolled_student_can_list_class_materials_with_safe_payload(self):
        self.current_user = self._user("student-user-1")

        response = self.client.get("/api/classes/class-1/materials")

        self.assertEqual(response.status_code, 200)
        materials = response.json()["materials"]
        self.assertEqual([material["filename"] for material in materials], ["practice-review.pdf", "fractions-notes.pdf"])
        material = materials[1]
        self.assertEqual(material["filename"], "fractions-notes.pdf")
        self.assertEqual(material["chunk_count"], 4)
        self.assertNotIn("vector_document_id", material)
        self.assertNotIn("error_message", material)
        self.assertNotIn("extraction_error", material)

    def test_unenrolled_student_cannot_list_class_materials(self):
        self.current_user = self._user("student-user-2")

        response = self.client.get("/api/classes/class-1/materials")

        self.assertEqual(response.status_code, 403)

    def test_teacher_keeps_full_material_payload(self):
        self.current_user = self._user("teacher-1")

        response = self.client.get("/api/classes/class-1/materials")

        self.assertEqual(response.status_code, 200)
        materials = response.json()["materials"]
        self.assertEqual(len(materials), 2)
        material = next(item for item in materials if item["filename"] == "fractions-notes.pdf")
        self.assertEqual(material["vector_document_id"], "class-1:doc-1")
        self.assertEqual(material["error_message"], "teacher-only detail")


if __name__ == "__main__":
    unittest.main()
