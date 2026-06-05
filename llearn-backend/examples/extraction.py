from __future__ import annotations

import openai

from document_processing.models import DocumentPage
from document_processing.pdf import extract_pdf_pages
from document_processing.text import clean_extracted_text
from examples.parsing import dedupe_examples, heuristic_extract_examples, parse_model_examples


EXTRACTION_MODEL = "gpt-4o"
MAX_EXTRACTION_CHARS = 18000
EXTRACTION_WINDOW_PAGES = 4
EXTRACTION_OVERLAP_PAGES = 1


def extract_example_problems(pdf_path: str) -> list[dict]:
    pages = extract_pdf_pages(pdf_path)
    if not pages:
        return []

    examples = []
    for page_window in _page_windows(pages):
        try:
            examples.extend(_extract_examples_from_window(page_window))
        except Exception:
            continue

    examples.extend(heuristic_extract_examples(pages))
    complete_examples = [
        example for example in examples
        if example.get("problem_text") and example.get("solution_text")
    ]
    return dedupe_examples(complete_examples)


def _extract_examples_from_window(pages: list[DocumentPage]) -> list[dict]:
    prompt = (
        "Extract every worked example problem from this textbook excerpt. "
        "Look for headings and labels such as Example, Solution, Answer, Checkpoint, Try It, Worked Example, "
        "or numbered examples. Include examples even when the solution continues onto the next page. "
        "Only include items that have both a problem prompt and an answer/worked solution in this text. "
        "Do not include unsolved exercises. Return JSON only with this shape: "
        "{\"examples\":[{\"problem_text\":\"...\",\"solution_text\":\"...\",\"page_start\":1,"
        "\"page_end\":1,\"confidence\":0.0}]}. "
        "Preserve equations and important givens. Use confidence from 0 to 1.\n\n"
        + "\n\n".join(_page_blocks(pages))
    )
    response = openai.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[
            {"role": "system", "content": "You extract structured worked examples from educational PDF text."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    return parse_model_examples(response.choices[0].message.content or "")


def _page_windows(pages: list[DocumentPage]) -> list[list[DocumentPage]]:
    windows = []
    step = max(1, EXTRACTION_WINDOW_PAGES - EXTRACTION_OVERLAP_PAGES)
    for start in range(0, len(pages), step):
        window = pages[start:start + EXTRACTION_WINDOW_PAGES]
        if window:
            windows.append(window)
    return windows


def _page_blocks(pages: list[DocumentPage]) -> list[str]:
    blocks = []
    total_length = 0
    for page in pages:
        block = f"Page {page['page']}:\n{clean_extracted_text(page['text'])}"
        if total_length + len(block) > MAX_EXTRACTION_CHARS:
            break
        blocks.append(block)
        total_length += len(block)
    return blocks
