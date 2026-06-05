from __future__ import annotations

import openai

from examples.parsing import bounded_float, parse_json_object


GRADING_MODEL = "gpt-4o"


def grade_example_attempt(*, problem_text: str, solution_text: str, submitted_answer: str) -> dict:
    response = openai.chat.completions.create(
        model=GRADING_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are grading a student's answer to a math example problem. "
                    "Use the provided solution as the rubric. Award correctness for mathematically equivalent "
                    "answers and sound reasoning. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Problem:\n"
                    f"{problem_text}\n\n"
                    "Reference solution:\n"
                    f"{solution_text}\n\n"
                    "Student answer:\n"
                    f"{submitted_answer}\n\n"
                    "Return JSON with keys: is_correct boolean, score number from 0 to 1, "
                    "feedback short student-facing string, reasoning_summary short teacher-facing string."
                ),
            },
        ],
        temperature=0.1,
    )
    payload = _parse_grading_payload(response.choices[0].message.content or "")
    score = bounded_float(payload.get("score"), default=1.0 if payload.get("is_correct") is True else 0.0)
    return {
        "is_correct": bool(payload.get("is_correct")) or score >= 0.85,
        "score": score,
        "feedback": str(payload.get("feedback") or "").strip() or "Your answer was reviewed.",
        "reasoning_summary": str(payload.get("reasoning_summary") or "").strip(),
    }


def _parse_grading_payload(raw: str) -> dict:
    return parse_json_object(raw)
