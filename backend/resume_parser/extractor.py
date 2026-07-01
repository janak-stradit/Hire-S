"""Extract raw text from PDF bytes.

Tries two pdfminer strategies and picks the result with more usable content.
"""
from __future__ import annotations

import io
import re

from pdfminer.high_level import extract_text, extract_text_to_fp
from pdfminer.layout import LAParams


def pdf_to_text(pdf_bytes: bytes) -> str:
    """Return the best raw text from a PDF (tries multiple LAParams presets)."""
    results = []
    for params in _PRESETS:
        try:
            buf = io.StringIO()
            extract_text_to_fp(
                io.BytesIO(pdf_bytes),
                buf,
                laparams=params,
                output_type="text",
                codec="utf-8",
            )
            text = buf.getvalue()
            results.append(text)
        except Exception:
            pass

    # Pick the extraction with the highest word count (more content = better)
    if not results:
        # Final fallback: default pdfminer
        try:
            return extract_text(io.BytesIO(pdf_bytes)) or ""
        except Exception:
            return ""

    best = max(results, key=_score)
    return _clean(best)


# ── LAParams presets ──────────────────────────────────────────────────────

_PRESETS = [
    # Standard single-column resume
    LAParams(line_margin=0.5, word_margin=0.1, char_margin=2.0),
    # Dense / narrow-column Naukri template
    LAParams(line_margin=0.3, word_margin=0.05, char_margin=1.5),
    # Wide / loose layout
    LAParams(line_margin=0.8, word_margin=0.2, char_margin=3.0),
]


# ── Scoring / cleaning ────────────────────────────────────────────────────

def _score(text: str) -> int:
    """Count real alphabetic words as a quality proxy."""
    return len(re.findall(r"[a-zA-Z]{3,}", text))


def _clean(text: str) -> str:
    """Collapse excessive blank lines and normalise whitespace."""
    lines = text.splitlines()
    out: list[str] = []
    blank_run = 0
    for ln in lines:
        stripped = ln.strip()
        if stripped:
            blank_run = 0
            out.append(stripped)
        else:
            blank_run += 1
            if blank_run <= 2:          # keep at most one blank line
                out.append("")
    return "\n".join(out).strip()
