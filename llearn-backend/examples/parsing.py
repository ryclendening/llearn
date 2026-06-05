from __future__ import annotations

import json
import re

from document_processing.models import DocumentPage
from document_processing.text import clean_extracted_text


def parse_model_examples(raw: str) -> list[dict]:
    payload = parse_json_object(raw)
    examples = payload.get("examples", []) if isinstance(payload, dict) else []
    if not isinstance(examples, list):
        return []
    return [normalize_example(example) for example in examples if isinstance(example, dict)]


def parse_json_object(raw: str) -> dict:
    payload = _loads_json(raw)
    return payload if isinstance(payload, dict) else {}


def heuristic_extract_examples(pages: list[DocumentPage]) -> list[dict]:
    examples = []
    full_text = "\n\n".join(f"[PAGE {page['page']}]\n{clean_extracted_text(page['text'])}" for page in pages)
    pattern = re.compile(
        r"(?:^|\n)\s*(?:[u•]\s*)?(?P<heading>(?:Example|EXAMPLE)\s+[0-9A-Za-z.\-]+)\b"
        r"(?P<body>.*?)(?=(?:\n\s*(?:[u•]\s*)?(?:Example|EXAMPLE)\s+[0-9A-Za-z.\-]+\b)|\Z)",
        re.DOTALL,
    )
    for match in pattern.finditer(full_text):
        body = f"{match.group('heading')} {match.group('body')}".strip()
        if len(body) < 80:
            continue
        solution_match = re.search(r"(?:^|\n)\s*(Solution|Answer)\b[.:]?\s*", body, flags=re.IGNORECASE)
        if not solution_match:
            continue
        problem_text = re.sub(r"^\[PAGE \d+\]\s*", "", body[:solution_match.start()]).strip()
        solution_text = _trim_solution(body[solution_match.end():].strip())
        if len(problem_text) < 20 or len(solution_text) < 20:
            continue
        pages_in_body = _pages_for_match(full_text, match.start(), f"{problem_text}\n{solution_text}")
        examples.append({
            "problem_text": problem_text,
            "solution_text": solution_text,
            "page_start": min(pages_in_body) if pages_in_body else None,
            "page_end": max(pages_in_body) if pages_in_body else None,
            "confidence": 0.65,
        })
    return examples


def dedupe_examples(examples: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for example in examples:
        normalized = normalize_example(example)
        key = re.sub(r"\W+", "", normalized["problem_text"].lower())[:180]
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped


def normalize_example(example: dict) -> dict:
    return {
        "problem_text": clean_extracted_text(str(example.get("problem_text") or "")).strip(),
        "solution_text": clean_extracted_text(str(example.get("solution_text") or "")).strip(),
        "page_start": _optional_int(example.get("page_start")),
        "page_end": _optional_int(example.get("page_end")),
        "confidence": bounded_float(example.get("confidence"), default=0.0),
    }


def bounded_float(value, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))


def _loads_json(raw: str):
    clean = raw.strip()
    clean = re.sub(r"^```(?:json)?", "", clean).strip()
    clean = re.sub(r"```$", "", clean).strip()
    return json.loads(clean)


def _pages_for_match(full_text: str, start: int, extracted_text: str) -> list[int]:
    pages = [int(value) for value in re.findall(r"\[PAGE (\d+)\]", extracted_text)]
    preceding_markers = list(re.finditer(r"\[PAGE (\d+)\]", full_text[:start]))
    if preceding_markers:
        pages.append(int(preceding_markers[-1].group(1)))
    return sorted(set(pages))


def _trim_solution(solution_text: str) -> str:
    end_marker_match = re.search(r"\s*⌅", solution_text)
    if end_marker_match:
        solution_text = solution_text[:end_marker_match.start()]
    stop_match = re.search(
        r"\n\s*(?:[‰u•]\s*)?(?:QUESTION|Question|Checkpoint|Try It|Summary|Exercises|Practice|Problems|Definition|Notation)\b",
        solution_text,
        flags=re.IGNORECASE,
    )
    if stop_match:
        solution_text = solution_text[:stop_match.start()]
    return solution_text.strip()


def _optional_int(value) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
