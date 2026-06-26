from __future__ import annotations

import json
import re
from typing import TypedDict


NON_EVIDENTIARY_CONFIRMATIONS = {
    "got it",
    "i get it",
    "i understand",
    "i think so",
    "makes sense",
    "okay",
    "ok",
    "sure",
    "understood",
    "yes",
    "yes i understand",
    "yep",
}


class StudentAssessmentEvidence(TypedDict):
    student_message: str
    preceding_tutor_message: str | None


def latest_student_evidence(messages: list) -> StudentAssessmentEvidence:
    """
    Select the latest student-authored message as the only mastery evidence.

    The tutor message immediately preceding it is included only so the assessor
    can interpret short answers and detect copied or prompted responses.
    """
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if not _has_role(message, "user"):
            continue

        preceding_tutor_message = None
        for prior in reversed(messages[:index]):
            if _has_role(prior, "assistant"):
                preceding_tutor_message = _content(prior)
                break

        return {
            "student_message": _content(message),
            "preceding_tutor_message": preceding_tutor_message,
        }

    return {"student_message": "", "preceding_tutor_message": None}


def student_message_can_change_mastery(evidence: StudentAssessmentEvidence) -> bool:
    """Reject obvious non-evidence before asking the model to update mastery."""
    student_message = _normalized_words(evidence["student_message"])
    if not student_message or student_message in NON_EVIDENTIARY_CONFIRMATIONS:
        return False

    tutor_message = _normalized_words(evidence["preceding_tutor_message"] or "")
    return not tutor_message or student_message != tutor_message


def assessment_system_prompt() -> str:
    return (
        "You update a student's mastery assessment after each tutoring exchange. "
        "Use the previous assessment as the baseline. The latest student message is "
        "the only new evidence allowed to change mastery. The preceding tutor message "
        "is reference-only context for interpreting what the student responded to; "
        "never treat tutor wording, explanations, hints, retrieved material, or answers "
        "as student evidence. Do not award mastery for short confirmations such as yes, "
        "okay, or I understand; requests for help; unsupported guesses; or text copied "
        "or lightly paraphrased from the tutor without independent reasoning. Only change "
        "an objective from 0 to 1 when the student message itself demonstrates clear, "
        "correct understanding or reasoning. Do not change a mastered objective back to "
        "0 unless the student message itself clearly shows the previous mastery was wrong. "
        "Return JSON only."
    )


def assessment_user_prompt(
    *,
    objective_list: str,
    previous_assessment: dict,
    evidence: StudentAssessmentEvidence,
) -> str:
    return (
        f"Objectives:\n{objective_list}\n\n"
        f"Previous assessment:\n{json.dumps(previous_assessment)}\n\n"
        "Latest student evidence (the only content that may justify a mastery change):\n"
        f"{json.dumps(evidence['student_message'])}\n\n"
        "Preceding tutor context (reference only; never count this as student evidence):\n"
        f"{json.dumps(evidence['preceding_tutor_message'])}\n\n"
        "Return ONLY a JSON object mapping every objective key to 1 or 0."
    )


def _has_role(message: object, role: str) -> bool:
    return isinstance(message, dict) and message.get("role") == role


def _content(message: dict) -> str:
    return str(message.get("content") or "").strip()


def _normalized_words(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()
