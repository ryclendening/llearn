from __future__ import annotations

import re


def clean_extracted_text(text: str) -> str:
    """Normalize common artifacts produced by PDF text extraction and OCR."""
    replacements = {
        "\x00": "-",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\u2212": "-",
        "\u2013": "-",
        "\u2014": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"w h e n", "when", text)
    text = re.sub(r"o v e r", "over", text)
    text = re.sub(r"i st h e", "is the", text)
    return text.strip()
