"""Prompt assembly for the local BitNet broker."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional


BROKER_POLICY_TEMPLATE = """Current local date: {current_date}

Operating rules:
- Never claim a specific built-in knowledge cutoff month or year.
- For claims about local code, files, tools, databases, runtime state, or current project status, rely on the provided evidence block.
- If needed evidence is missing, say what is missing instead of guessing.
- Do not invent file contents, command output, citations, or tool results.
- Distinguish stable background knowledge from time-sensitive facts.
"""


def get_current_date_string() -> str:
    """Return the local date used in the system prompt guard."""
    return datetime.now().astimezone().strftime("%B %-d, %Y")


def build_system_prompt(base_system_prompt: str) -> str:
    """Combine the base system prompt with local runtime policy."""
    policy = BROKER_POLICY_TEMPLATE.format(current_date=get_current_date_string()).strip()
    base = (base_system_prompt or "You are a precise local assistant.").strip()
    return base + "\n\n" + policy


def format_evidence(evidence_items: Iterable[Dict[str, str]]) -> str:
    """Render evidence items into a bounded, model-friendly text block."""
    blocks: List[str] = []
    for item in evidence_items:
        source = item.get("source", "unknown")
        kind = item.get("kind", "evidence")
        content = item.get("content", "").strip()
        if not content:
            continue
        blocks.append(f"[{kind}] {source}\n{content}")
    if not blocks:
        return "No evidence was provided."
    return "\n\n".join(blocks)


def build_messages(
    system_prompt: str,
    user_prompt: str,
    evidence_items: Iterable[Dict[str, str]],
    required_sections: Optional[Iterable[str]] = None,
) -> List[Dict[str, str]]:
    """Build chat messages for llama-server."""
    user_parts = [
        "Evidence:\n%s" % format_evidence(evidence_items),
        "Task:\n%s" % user_prompt.strip(),
    ]

    sections = [section.strip() for section in (required_sections or []) if section.strip()]
    if sections:
        user_parts.append(
            "Required headings:\n%s" % "\n".join("- %s" % section for section in sections)
        )
        user_parts.append(
            "Output contract:\n"
            "- Return Markdown only.\n"
            "- Start immediately with the first required heading.\n"
            "- Use the required headings exactly as written and in the same order.\n"
            "- Do not add any preamble before the first heading.\n"
            '- If evidence is missing, write "Not enough evidence provided." under that heading.'
        )
        user_parts.append(
            "Required template:\n%s"
            % "\n\n".join("# %s\n..." % section for section in sections)
        )

    return [
        {
            "role": "system",
            "content": build_system_prompt(system_prompt),
        },
        {
            "role": "user",
            "content": "\n\n".join(user_parts),
        },
    ]
