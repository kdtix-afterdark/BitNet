"""Prompt assembly for the local BitNet broker."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional


BROKER_POLICY_TEMPLATE = """Current local date: {current_date}

Operating rules:
- Respond in English unless the user explicitly requests another language.
- Never claim a specific built-in knowledge cutoff month or year.
- For claims about local code, files, tools, databases, runtime state, or current project status, rely on the provided evidence block.
- If needed evidence is missing, say what is missing instead of guessing.
- Do not invent file contents, command output, citations, or tool results.
- Distinguish stable background knowledge from time-sensitive facts.
"""


def get_current_date_string() -> str:
    """Return the local date used in the system prompt guard."""
    return datetime.now().astimezone().strftime("%B %-d, %Y")


def format_tool_manifest(
    tool_manifest: Iterable[Dict[str, str]],
    broker_controls_tools: bool,
) -> str:
    """Render a compact model-facing broker tool manifest."""
    items = list(tool_manifest)
    if not items:
        return ""

    control_line = (
        "Broker tool control mode: broker is in control of tool execution for this turn."
        if broker_controls_tools
        else "Broker tool control mode: broker is not in control for this turn."
    )
    usage_rules = (
        "- Do not claim to have executed tools yourself.\n"
        "- If current evidence is missing, say which broker tool would help."
        if not broker_controls_tools
        else "- Do not claim to have executed tools yourself.\n"
        "- Rely on provided evidence and note missing evidence when needed."
    )
    lines = [
        control_line,
        "Known broker tools:",
    ]
    for item in items:
        lines.append("- %s: %s" % (item["name"], item["description"]))
    lines.append("Tool usage rules:\n%s" % usage_rules)
    return "\n".join(lines)


def build_system_prompt(
    base_system_prompt: str,
    tool_manifest: Optional[Iterable[Dict[str, str]]] = None,
    broker_controls_tools: bool = False,
) -> str:
    """Combine the base system prompt with local runtime policy."""
    policy = BROKER_POLICY_TEMPLATE.format(current_date=get_current_date_string()).strip()
    base = (base_system_prompt or "You are a precise local assistant.").strip()
    manifest_block = format_tool_manifest(tool_manifest or [], broker_controls_tools).strip()

    blocks = [base, policy]
    if manifest_block:
        blocks.append(manifest_block)
    return "\n\n".join(block for block in blocks if block)


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
    tool_manifest: Optional[Iterable[Dict[str, str]]] = None,
    broker_controls_tools: bool = False,
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
            "content": build_system_prompt(
                system_prompt,
                tool_manifest=tool_manifest,
                broker_controls_tools=broker_controls_tools,
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(user_parts),
        },
    ]
