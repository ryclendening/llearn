from __future__ import annotations

import json
import re

import openai

from vector_db.pipeline import extract_pages


EXTRACTION_MODEL = "gpt-4o"
GRADING_MODEL = "gpt-4o"
MAX_EXTRACTION_CHARS = 18000
EXTRACTION_WINDOW_PAGES = 4
EXTRACTION_OVERLAP_PAGES = 1


def extract_example_problems(pdf_path: str) -> list[dict]:
    pages = extract_pages(pdf_path)
    if not pages:
        return []

    examples = []
    for page_window in _page_windows(pages):
        try:
            examples.extend(_extract_examples_from_window(page_window))
        except Exception:
            continue

    examples.extend(_heuristic_extract_examples(pages))
    return _dedupe_examples([example for example in examples if example.get("problem_text") and example.get("solution_text")])


def _extract_examples_from_window(pages: list[dict]) -> list[dict]:
    page_blocks = _page_blocks(pages)
    prompt = (
        "Extract every worked example problem from this textbook excerpt. "
        "Look for headings and labels such as Example, Solution, Answer, Checkpoint, Try It, Worked Example, "
        "or numbered examples. Include examples even when the solution continues onto the next page. "
        "Only include items that have both a problem prompt and an answer/worked solution in this text. "
        "Do not include unsolved exercises. Return JSON only with this shape: "
        "{\"examples\":[{\"problem_text\":\"...\",\"solution_text\":\"...\",\"page_start\":1,"
        "\"page_end\":1,\"confidence\":0.0}]}. "
        "Preserve equations and important givens. Use confidence from 0 to 1.\n\n"
        + "\n\n".join(page_blocks)
    )
    response = openai.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[
            {"role": "system", "content": "You extract structured worked examples from educational PDF text."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    payload = _loads_json(response.choices[0].message.content or "")
    examples = payload.get("examples", []) if isinstance(payload, dict) else []
    if not isinstance(examples, list):
        return []
    return [_normalize_example(example) for example in examples if isinstance(example, dict)]


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
    payload = _loads_json(response.choices[0].message.content or "")
    if not isinstance(payload, dict):
        payload = {}
    score = _bounded_float(payload.get("score"), default=1.0 if payload.get("is_correct") is True else 0.0)
    return {
        "is_correct": bool(payload.get("is_correct")) or score >= 0.85,
        "score": score,
        "feedback": str(payload.get("feedback") or "").strip() or "Your answer was reviewed.",
        "reasoning_summary": str(payload.get("reasoning_summary") or "").strip(),
    }


def _loads_json(raw: str):
    clean = raw.strip()
    clean = re.sub(r"^```(?:json)?", "", clean).strip()
    clean = re.sub(r"```$", "", clean).strip()
    return json.loads(clean)


def _page_windows(pages: list[dict]) -> list[list[dict]]:
    windows = []
    step = max(1, EXTRACTION_WINDOW_PAGES - EXTRACTION_OVERLAP_PAGES)
    for start in range(0, len(pages), step):
        window = pages[start:start + EXTRACTION_WINDOW_PAGES]
        if window:
            windows.append(window)
    return windows


def _page_blocks(pages: list[dict]) -> list[str]:
    blocks = []
    total_length = 0
    for page in pages:
        block = f"Page {page['page']}:\n{page['text']}"
        if total_length + len(block) > MAX_EXTRACTION_CHARS:
            break
        blocks.append(block)
        total_length += len(block)
    return blocks


def _heuristic_extract_examples(pages: list[dict]) -> list[dict]:
    examples = []
    full_text = "\n\n".join(f"[PAGE {page['page']}]\n{page['text']}" for page in pages)
    pattern = re.compile(
        r"(?:^|\n)(?:Example|EXAMPLE)\s+([0-9A-Za-z.\-]+)?(?P<body>.*?)(?=(?:\n(?:Example|EXAMPLE)\s+[0-9A-Za-z.\-]+)|\Z)",
        re.DOTALL,
    )
    for match in pattern.finditer(full_text):
        body = match.group("body").strip()
        if len(body) < 80:
            continue
        solution_match = re.search(r"\b(Solution|Answer)\b\s*:?\s*", body, flags=re.IGNORECASE)
        if not solution_match:
            continue
        problem_text = body[:solution_match.start()].strip()
        solution_text = body[solution_match.end():].strip()
        problem_text = re.sub(r"^\[PAGE \d+\]\s*", "", problem_text).strip()
        solution_text = _trim_solution(solution_text)
        if len(problem_text) < 20 or len(solution_text) < 20:
            continue
        pages_in_body = [int(value) for value in re.findall(r"\[PAGE (\d+)\]", body)]
        examples.append({
            "problem_text": problem_text,
            "solution_text": solution_text,
            "page_start": min(pages_in_body) if pages_in_body else None,
            "page_end": max(pages_in_body) if pages_in_body else None,
            "confidence": 0.65,
        })
    return examples


def _trim_solution(solution_text: str) -> str:
    stop_match = re.search(r"\n\s*(?:Checkpoint|Try It|Exercises|Practice|Problems)\b", solution_text, flags=re.IGNORECASE)
    if stop_match:
        solution_text = solution_text[:stop_match.start()]
    return solution_text.strip()


def _dedupe_examples(examples: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for example in examples:
        normalized = _normalize_example(example)
        key = re.sub(r"\W+", "", normalized["problem_text"].lower())[:180]
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped


def _normalize_example(example: dict) -> dict:
    return {
        "problem_text": str(example.get("problem_text") or "").strip(),
        "solution_text": str(example.get("solution_text") or "").strip(),
        "page_start": _optional_int(example.get("page_start")),
        "page_end": _optional_int(example.get("page_end")),
        "confidence": _bounded_float(example.get("confidence"), default=0.0),
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
