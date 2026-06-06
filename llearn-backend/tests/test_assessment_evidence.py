from __future__ import annotations

import unittest

from assessment.evidence import (
    assessment_system_prompt,
    assessment_user_prompt,
    latest_student_evidence,
    student_message_can_change_mastery,
)


class AssessmentEvidenceTests(unittest.TestCase):
    def test_latest_student_message_is_only_evidence_and_new_tutor_reply_is_excluded(self):
        evidence = latest_student_evidence([
            {"role": "assistant", "content": "A denominator tells how many equal parts make a whole."},
            {"role": "user", "content": "It is the number of equal parts in the whole."},
            {"role": "assistant", "content": "Exactly. You clearly understand denominators."},
        ])

        self.assertEqual(evidence["student_message"], "It is the number of equal parts in the whole.")
        self.assertEqual(
            evidence["preceding_tutor_message"],
            "A denominator tells how many equal parts make a whole.",
        )

    def test_confirmation_remains_student_evidence_without_tutor_answer_becoming_evidence(self):
        evidence = latest_student_evidence([
            {"role": "assistant", "content": "The answer is 12 because 3 times 4 equals 12."},
            {"role": "user", "content": "Yes, I understand."},
            {"role": "assistant", "content": "Great work."},
        ])

        self.assertEqual(evidence["student_message"], "Yes, I understand.")
        self.assertNotIn("answer is 12", evidence["student_message"])

    def test_no_student_message_produces_empty_evidence(self):
        evidence = latest_student_evidence([{"role": "assistant", "content": "Welcome."}])

        self.assertEqual(evidence, {"student_message": "", "preceding_tutor_message": None})

    def test_prompt_marks_tutor_context_as_reference_only(self):
        prompt = assessment_user_prompt(
            objective_list="objective_1: Explain fractions",
            previous_assessment={"objective_1": 0},
            evidence={
                "student_message": "A fraction represents part of a whole.",
                "preceding_tutor_message": "What does a fraction represent?",
            },
        )

        self.assertIn("only content that may justify a mastery change", prompt)
        self.assertIn("reference only; never count this as student evidence", prompt)

    def test_system_prompt_rejects_confirmations_and_copied_tutor_text(self):
        prompt = assessment_system_prompt()

        self.assertIn("short confirmations", prompt)
        self.assertIn("copied", prompt)
        self.assertIn("student message is the only new evidence", prompt)

    def test_confirmation_cannot_change_mastery(self):
        self.assertFalse(student_message_can_change_mastery({
            "student_message": "Yes, I understand.",
            "preceding_tutor_message": "A fraction represents part of a whole.",
        }))

    def test_exact_copy_of_tutor_message_cannot_change_mastery(self):
        self.assertFalse(student_message_can_change_mastery({
            "student_message": "A fraction represents part of a whole!",
            "preceding_tutor_message": "A fraction represents part of a whole.",
        }))

    def test_independent_student_reasoning_can_change_mastery(self):
        self.assertTrue(student_message_can_change_mastery({
            "student_message": "The denominator is four because the whole was divided into four equal pieces.",
            "preceding_tutor_message": "What does the denominator tell you?",
        }))


if __name__ == "__main__":
    unittest.main()
