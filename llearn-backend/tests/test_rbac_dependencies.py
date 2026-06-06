from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from auth.dependencies import require_role, require_student_enrollment, require_teacher_owner


class RbacDependencyTests(unittest.TestCase):
    def test_role_dependency_rejects_wrong_role(self):
        dependency = require_role("teacher")
        with self.assertRaises(HTTPException) as raised:
            dependency(SimpleNamespace(role="student"))
        self.assertEqual(raised.exception.status_code, 403)

    def test_teacher_owner_rejects_another_teachers_class(self):
        lesson = SimpleNamespace(owner_user_id="teacher-2")
        with patch("auth.dependencies.get_lesson", return_value=lesson):
            with self.assertRaises(HTTPException) as raised:
                require_teacher_owner("class-1", SimpleNamespace(id="teacher-1", role="teacher"), Mock())
        self.assertEqual(raised.exception.status_code, 403)

    def test_student_enrollment_rejects_unenrolled_class(self):
        student_record = SimpleNamespace(enrollments=[SimpleNamespace(lesson_id="class-1")])
        with self.assertRaises(HTTPException) as raised:
            require_student_enrollment("class-2", SimpleNamespace(role="student", student=student_record), Mock())
        self.assertEqual(raised.exception.status_code, 403)

    def test_student_enrollment_accepts_enrolled_class(self):
        user = SimpleNamespace(role="student", student=SimpleNamespace(enrollments=[SimpleNamespace(lesson_id="class-1")]))
        self.assertIs(require_student_enrollment("class-1", user, Mock()), user)


if __name__ == "__main__":
    unittest.main()
