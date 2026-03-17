"""Deterministic output cleanup, repair, and checks for broker responses."""

from __future__ import annotations

import json
import re
from typing import Dict, Iterable, List, Optional, Tuple


_MARKDOWN_FENCE_RE = re.compile(r"^```(?:markdown|md)?\s*\n(?P<body>[\s\S]*?)\n```$")
_HEADING_RE = re.compile(r"^(?P<level>#+)\s+(?P<title>.+?)\s*$", flags=re.MULTILINE)


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


def extract_sections(text: str) -> Dict[str, str]:
    """Return a mapping of markdown heading text to section body."""
    matches = list(_HEADING_RE.finditer(text))
    sections: Dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group("title").strip()
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[body_start:body_end].strip()
    return sections


def repair_required_sections(
    text: str,
    required_sections: Iterable[str],
    artifact_id: str,
) -> str:
    """Guarantee the required heading scaffold even when model output is weak."""
    required = [section.strip() for section in required_sections if section.strip()]
    if not required:
        return normalize_markdown(text)

    existing_sections = extract_sections(text)
    repaired_blocks = []
    for section in required:
        body = existing_sections.get(section, "").strip()
        if not body:
            if section.lower() == "metadata":
                body = (
                    f"- artifact_id: {artifact_id}\n"
                    "- status: incomplete\n"
                    "- note: broker inserted this section because the model did not"
                    " satisfy the required heading contract"
                )
            else:
                body = "Not enough grounded content was produced for this required section."
        repaired_blocks.append(f"# {section}\n{body}")

    return "\n\n".join(repaired_blocks).rstrip() + "\n"


def _parse_evidence_payload(content: str) -> Optional[Dict[str, object]]:
    """Best-effort parse of one JSON evidence payload."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def extract_first_markdown_title_from_evidence(
    evidence_items: Iterable[Dict[str, str]],
) -> Optional[str]:
    """Extract the first markdown H1 title found in evidence payload content."""
    for item in evidence_items:
        payload = _parse_evidence_payload(item.get("content", ""))
        if not payload:
            continue
        raw_content = payload.get("content")
        if not isinstance(raw_content, str):
            continue
        match = re.search(r"^#\s+(.+?)\s*$", raw_content, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def repair_chat_response(
    prompt: str,
    text: str,
    evidence_items: Iterable[Dict[str, str]],
) -> Tuple[str, bool, Optional[str]]:
    """Apply deterministic repairs for simple extractive grounded chat tasks."""
    normalized = strip_markdown_fence(text).strip()
    lowered_prompt = prompt.lower()

    title_only_request = (
        "title only" in lowered_prompt
        or "document title only" in lowered_prompt
        or "answer with the document title" in lowered_prompt
    )
    if title_only_request:
        title = extract_first_markdown_title_from_evidence(evidence_items)
        if title:
            return title, True, "extracted_title_from_evidence"

    return normalized, False, None
