"""Deterministic output cleanup, repair, and checks for broker responses."""

from __future__ import annotations

import json
import re
from typing import Dict, Iterable, List, Optional, Tuple


_MARKDOWN_FENCE_RE = re.compile(r"^```(?:markdown|md)?\s*\n(?P<body>[\s\S]*?)\n```$")
_HEADING_RE = re.compile(r"^(?P<level>#+)\s+(?P<title>.+?)\s*$", flags=re.MULTILINE)
_ROLE_LABEL_SPILLOVER_RE = re.compile(r"\n\s*(?:User|Assistant|System):\s", flags=re.IGNORECASE)
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")


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


def extract_tool_names_from_evidence(evidence_items: Iterable[Dict[str, str]]) -> List[str]:
    """Return the distinct tool names recorded in evidence sources."""
    tool_names: List[str] = []
    for item in evidence_items:
        source = item.get("source", "")
        if not source.startswith("tool:"):
            continue
        tool_name = source.split(":", 1)[1].strip()
        if tool_name and tool_name not in tool_names:
            tool_names.append(tool_name)
    return tool_names


def extract_paths_from_evidence(evidence_items: Iterable[Dict[str, str]]) -> List[str]:
    """Return distinct workspace-relative paths found in evidence payloads."""
    paths: List[str] = []
    for item in evidence_items:
        payload = _parse_evidence_payload(item.get("content", ""))
        if not payload:
            continue
        path_value = payload.get("path")
        if isinstance(path_value, str) and path_value not in paths:
            paths.append(path_value)

        matches = payload.get("matches")
        if isinstance(matches, list):
            for match in matches:
                if not isinstance(match, dict):
                    continue
                match_path = match.get("path")
                if isinstance(match_path, str) and match_path not in paths:
                    paths.append(match_path)

        entries = payload.get("entries")
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                entry_path = entry.get("path")
                if isinstance(entry_path, str) and entry_path not in paths:
                    paths.append(entry_path)
    return paths


def extract_directory_entries_from_evidence(
    evidence_items: Iterable[Dict[str, str]],
    max_entries: int = 10,
) -> List[str]:
    """Return directory entry paths from list_directory evidence."""
    entries_out: List[str] = []
    for item in evidence_items:
        payload = _parse_evidence_payload(item.get("content", ""))
        if not payload:
            continue
        entries = payload.get("entries")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_path = entry.get("path")
            if isinstance(entry_path, str) and entry_path not in entries_out:
                entries_out.append(entry_path)
            if len(entries_out) >= max_entries:
                return entries_out
    return entries_out


def extract_match_count_from_evidence(evidence_items: Iterable[Dict[str, str]]) -> Optional[int]:
    """Return the total number of search matches represented in evidence."""
    count = 0
    found = False
    for item in evidence_items:
        payload = _parse_evidence_payload(item.get("content", ""))
        if not payload:
            continue
        matches = payload.get("matches")
        if not isinstance(matches, list):
            continue
        count += len(matches)
        found = True
    return count if found else None


def extract_truncated_flag_from_evidence(
    evidence_items: Iterable[Dict[str, str]],
) -> Optional[bool]:
    """Return whether any evidence payload indicates truncation."""
    saw_flag = False
    any_truncated = False
    for item in evidence_items:
        payload = _parse_evidence_payload(item.get("content", ""))
        if not payload:
            continue
        truncated = payload.get("truncated")
        if isinstance(truncated, bool):
            saw_flag = True
            any_truncated = any_truncated or truncated
    return any_truncated if saw_flag else None


def _format_scalar_response(value: str, prompt: str) -> str:
    """Format one extracted scalar according to a simple prompt contract."""
    lowered_prompt = prompt.lower()
    if "yes/no" in lowered_prompt or lowered_prompt.startswith("is ") or lowered_prompt.startswith("are "):
        return value
    if "only" in lowered_prompt or "just" in lowered_prompt or "number" in lowered_prompt:
        return value
    return value


def _format_list_response(values: List[str], prompt: str) -> str:
    """Format a short extracted list response."""
    lowered_prompt = prompt.lower()
    if "one per line" in lowered_prompt or "newline" in lowered_prompt:
        return "\n".join(values)
    return ", ".join(values)


def _prompt_requests_transcript(prompt: str) -> bool:
    lowered = prompt.lower()
    triggers = (
        "transcript",
        "chat log",
        "dialogue",
        "dialog",
        "speaker label",
        "role label",
        "conversation between",
        "write a conversation",
        "write a transcript",
        "script format",
        "screenplay",
        "user:",
        "assistant:",
    )
    return any(trigger in lowered for trigger in triggers)


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _split_paragraphs(text: str) -> List[str]:
    return [paragraph.strip() for paragraph in _PARAGRAPH_SPLIT_RE.split(text.strip()) if paragraph.strip()]


def trim_repeated_assistant_prefix(
    prompt: str,
    text: str,
    conversation_history: Optional[Iterable[Dict[str, str]]] = None,
) -> Optional[str]:
    """Trim a stale leading assistant block copied from recent assistant history."""
    if _prompt_requests_transcript(prompt):
        return None

    normalized_text = text.strip()
    if not normalized_text:
        return None

    recent_assistant_responses = [
        str(message.get("content", "")).strip()
        for message in conversation_history or []
        if str(message.get("role", "")).strip() == "assistant"
        and str(message.get("content", "")).strip()
    ]
    if not recent_assistant_responses:
        return None

    for prior_raw in sorted(recent_assistant_responses[-4:], key=len, reverse=True):
        prior = _normalize_space(prior_raw)
        if len(prior_raw) < 24:
            continue
        if normalized_text == prior_raw:
            continue
        if normalized_text.startswith(prior_raw + "\n\n"):
            trimmed = normalized_text[len(prior_raw) :].lstrip()
            if len(trimmed) >= 24:
                return trimmed
        if _normalize_space(normalized_text).startswith(prior + " "):
            paragraphs = _split_paragraphs(normalized_text)
            trimmed = "\n\n".join(paragraphs[1:]).strip()
            if len(trimmed) >= 24:
                return trimmed

    paragraphs = _split_paragraphs(normalized_text)
    if len(paragraphs) < 2:
        return None

    first_paragraph = _normalize_space(paragraphs[0])
    if any(first_paragraph == _normalize_space(prior) for prior in recent_assistant_responses[-4:]):
        trimmed = "\n\n".join(paragraphs[1:]).strip()
        if len(trimmed) >= 24:
            return trimmed
    return None


def trim_role_label_spillover(prompt: str, text: str) -> Optional[str]:
    """Trim accidental raw transcript spillover from a normal assistant reply."""
    if _prompt_requests_transcript(prompt):
        return None

    match = _ROLE_LABEL_SPILLOVER_RE.search(text)
    if match is None:
        return None

    trimmed = text[: match.start()].rstrip()
    if len(trimmed) < 24:
        return None
    return trimmed


def collapse_duplicate_paragraphs(prompt: str, text: str) -> Optional[str]:
    """Collapse obvious duplicate paragraph loops in normal assistant replies."""
    if _prompt_requests_transcript(prompt):
        return None

    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 3:
        return None

    kept: List[str] = []
    seen_long: set[str] = set()
    removed = False
    for paragraph in paragraphs:
        normalized = _normalize_space(paragraph)
        is_long = len(normalized) >= 120
        if is_long and normalized in seen_long:
            removed = True
            continue
        kept.append(paragraph)
        if is_long:
            seen_long.add(normalized)

    if not removed:
        return None

    collapsed = "\n\n".join(kept).strip()
    if len(collapsed) < 24:
        return None
    return collapsed


def repair_chat_response(
    prompt: str,
    text: str,
    evidence_items: Iterable[Dict[str, str]],
    conversation_history: Optional[Iterable[Dict[str, str]]] = None,
) -> Tuple[str, bool, Optional[str]]:
    """Apply deterministic repairs for simple extractive grounded chat tasks."""
    normalized = strip_markdown_fence(text).strip()
    lowered_prompt = prompt.lower()
    working = normalized
    repairs: List[str] = []

    trimmed_spillover = trim_role_label_spillover(prompt, working)
    if trimmed_spillover is not None:
        return trimmed_spillover, True, "trimmed_role_label_spillover"

    trimmed_prefix = trim_repeated_assistant_prefix(
        prompt,
        working,
        conversation_history=conversation_history,
    )
    if trimmed_prefix is not None:
        working = trimmed_prefix
        repairs.append("trimmed_repeated_assistant_prefix")

    collapsed_duplicates = collapse_duplicate_paragraphs(prompt, working)
    if collapsed_duplicates is not None:
        working = collapsed_duplicates
        repairs.append("collapsed_duplicate_paragraphs")

    if repairs:
        return working, True, "+".join(repairs)

    if (
        "title only" in lowered_prompt
        or "document title only" in lowered_prompt
        or "answer with the document title" in lowered_prompt
    ):
        title = extract_first_markdown_title_from_evidence(evidence_items)
        if title:
            return _format_scalar_response(title, prompt), True, "extracted_title_from_evidence"

    if "first heading" in lowered_prompt or "top heading" in lowered_prompt:
        heading = extract_first_markdown_title_from_evidence(evidence_items)
        if heading:
            return _format_scalar_response(heading, prompt), True, "extracted_first_heading_from_evidence"

    if (
        "tool names" in lowered_prompt
        or "which tools" in lowered_prompt
        or "tools were used" in lowered_prompt
    ):
        tool_names = extract_tool_names_from_evidence(evidence_items)
        if tool_names:
            return _format_list_response(tool_names, prompt), True, "extracted_tool_names_from_evidence"

    if (
        "file path" in lowered_prompt
        or "what path" in lowered_prompt
        or "which path" in lowered_prompt
    ):
        paths = extract_paths_from_evidence(evidence_items)
        if paths:
            return _format_scalar_response(paths[0], prompt), True, "extracted_path_from_evidence"

    if (
        "directory entries" in lowered_prompt
        or "list files" in lowered_prompt
        or "list entries" in lowered_prompt
    ):
        entries = extract_directory_entries_from_evidence(evidence_items)
        if entries:
            return _format_list_response(entries, prompt), True, "extracted_directory_entries_from_evidence"

    if (
        "how many matches" in lowered_prompt
        or "number of matches" in lowered_prompt
        or "count of matches" in lowered_prompt
    ):
        match_count = extract_match_count_from_evidence(evidence_items)
        if match_count is not None:
            return _format_scalar_response(str(match_count), prompt), True, "extracted_match_count_from_evidence"

    if (
        "is it truncated" in lowered_prompt
        or "was it truncated" in lowered_prompt
        or "were results truncated" in lowered_prompt
    ):
        truncated = extract_truncated_flag_from_evidence(evidence_items)
        if truncated is not None:
            return "Yes" if truncated else "No", True, "extracted_truncation_flag_from_evidence"

    return working, False, None
