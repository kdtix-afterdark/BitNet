"""Deterministic output cleanup and checks for broker responses."""

from __future__ import annotations

import re
from typing import Iterable, List, Tuple


_MARKDOWN_FENCE_RE = re.compile(r"^```(?:markdown|md)?\s*\n(?P<body>[\s\S]*?)\n```$")


def strip_markdown_fence(text: str) -> str:
    """Remove an outer markdown fence if the model wrapped the whole answer."""
    stripped = text.strip()
    match = _MARKDOWN_FENCE_RE.match(stripped)
    if match:
        return match.group("body").strip()
    return stripped


def normalize_markdown(text: str) -> str:
    """Apply basic deterministic cleanup to markdown output."""
    cleaned = strip_markdown_fence(text)
    return cleaned.rstrip() + "\n"


def find_missing_sections(text: str, required_sections: Iterable[str]) -> List[str]:
    """Return required markdown headings that are missing from the draft."""
    missing = []
    for section in required_sections:
        pattern = r"^#+\s+%s\s*$" % re.escape(section)
        if re.search(pattern, text, flags=re.MULTILINE) is None:
            missing.append(section)
    return missing


def postprocess_markdown(
    text: str, required_sections: Iterable[str]
) -> Tuple[str, List[str]]:
    """Return cleaned markdown plus any missing required headings."""
    cleaned = normalize_markdown(text)
    missing = find_missing_sections(cleaned, required_sections)
    return cleaned, missing

