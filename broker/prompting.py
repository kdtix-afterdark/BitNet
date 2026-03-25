"""Prompt assembly and context compiler for the local BitNet broker.

Context compiler assembly (TASK-LAH-004)
-----------------------------------------
The context compiler transforms ledger state, a run profile, tools, and
selected memory evidence into the model-facing messages list.

Inputs
~~~~~~
- ``SessionLedger`` — append-only event log; the compiler filters events by
  ``visibility.visible_to_model`` before including them.
- ``RunProfile`` — gates which tool categories appear in the manifest.
- ``user_prompt`` — the current-turn question from the caller.
- ``tool_manifest`` — full broker tool list; gated by profile before injection.
- ``evidence_items`` — explicit evidence gathered by deterministic tool calls.
- ``memory_evidence`` — evidence retrieved from the memory subsystem.
- ``broker_controls_tools`` — toggles the broker-control-mode line in the
  tool-manifest block.

Outputs
~~~~~~~
A ``List[Dict[str, str]]`` of chat messages ready for llama-server:

1. ``{"role": "system", "content": <system prompt + policy + gated tool manifest>}``
2. (optional) Alternating ``"user"`` / ``"assistant"`` history messages drawn
   from model-visible ``USER_MESSAGE`` and ``ASSISTANT_MESSAGE`` ledger events.
3. ``{"role": "user", "content": "Evidence:\\n…\\n\\nTask:\\n<user_prompt>"}``
   — the current-turn user message, always containing an evidence block.

Model-facing inclusion rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Only ``USER_MESSAGE`` and ``ASSISTANT_MESSAGE`` ledger events appear as
conversation-history turns.  All other model-visible event kinds
(``USER_CONTEXT``, ``TOOL_INVOKED``, ``TOOL_RESULT``, ``MEMORY_READ``) are
surfaced as evidence items inside the current-turn user message, not as
standalone turns.

Ops-only events (``SESSION_OPENED``, ``SESSION_CLOSED``, ``PROFILE_APPLIED``,
``CONSTRAINT_APPLIED``, ``ASSISTANT_THINKING``, ``MEMORY_WRITE``,
``MEMORY_SYNC``, ``ARTIFACT_DELETED``) are never injected into the model
context.

The compiler boundary is **not** a pure transcript replay: the system policy
block (``BROKER_POLICY_TEMPLATE``) and an evidence section are always present
in the output, even when the ledger contains only ops-only events.

Reference: docs/plans/artifacts/local_llm_agent_harness_modern_stacks/
TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional

if TYPE_CHECKING:
    from .durable_state import SessionLedger
    from .run_profile import RunProfile


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


_MAX_LOW_INFO_REPLY_LENGTH = 160


def _normalize_message_content(content: str) -> str:
    """Collapse whitespace so repeated low-information replies compare cleanly."""
    return " ".join(content.split())


def _is_low_information_assistant_reply(content: str) -> bool:
    """Return True for short assistant boilerplate that should not be replayed repeatedly."""
    normalized = _normalize_message_content(content)
    if not normalized or len(normalized) > _MAX_LOW_INFO_REPLY_LENGTH:
        return False
    if "```" in content or "`" in content:
        return False
    markers = (
        "how can i assist you today",
        "how can i help you today",
        "you can call me",
        "i'm bitnet",
    )
    lowered = normalized.lower()
    return any(marker in lowered for marker in markers)


def shape_conversation_history(
    conversation_history: Optional[Iterable[Dict[str, str]]],
) -> List[Dict[str, str]]:
    """Return a model-facing history that keeps user turns but collapses repeated boilerplate."""
    shaped: List[Dict[str, str]] = []
    seen_assistant_boilerplate: set = set()

    for message in conversation_history or []:
        role = message.get("role", "").strip()
        content = message.get("content", "").strip()
        if role not in {"user", "assistant"} or not content:
            continue

        normalized = _normalize_message_content(content)
        if role == "assistant" and _is_low_information_assistant_reply(content):
            if normalized in seen_assistant_boilerplate:
                continue
            seen_assistant_boilerplate.add(normalized)

        shaped.append({"role": role, "content": content})

    return shaped


def build_messages(
    system_prompt: str,
    user_prompt: str,
    evidence_items: Iterable[Dict[str, str]],
    conversation_history: Optional[Iterable[Dict[str, str]]] = None,
    conversation_summary: Optional[str] = None,
    summarized_turn_count: int = 0,
    required_sections: Optional[Iterable[str]] = None,
    tool_manifest: Optional[Iterable[Dict[str, str]]] = None,
    broker_controls_tools: bool = False,
    grounded_user_prompt: bool = True,
) -> List[Dict[str, str]]:
    """Build chat messages for llama-server.

    When *conversation_history* is provided the prior turns are injected
    between the system message and the current user message so the model
    retains context across a multi-turn session.
    """
    user_parts: List[str] = []
    if grounded_user_prompt:
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

    system_content = build_system_prompt(
        system_prompt,
        tool_manifest=tool_manifest,
        broker_controls_tools=broker_controls_tools,
    )
    summary_text = (conversation_summary or "").strip()
    if summary_text:
        heading = "Recovered conversation summary for earlier turns omitted from verbatim history"
        if summarized_turn_count > 0:
            heading += " (%d turns)" % summarized_turn_count
        system_content = "%s\n\n%s:\n%s" % (system_content, heading, summary_text)

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]

    for message in shape_conversation_history(conversation_history):
        messages.append(message)

    messages.append(
        {
            "role": "user",
            "content": "\n\n".join(user_parts) if grounded_user_prompt else user_prompt.strip(),
        }
    )
    return messages


# ---------------------------------------------------------------------------
# Tool name → profile flag mapping
# ---------------------------------------------------------------------------

#: Maps each known broker tool name to the ``ToolAccess`` attribute that gates
#: its inclusion.  Tools not in this table are excluded by default (safe-fail).
_TOOL_PROFILE_FLAG: Dict[str, str] = {
    # Filesystem read tools
    "list_directory":        "filesystem_read",
    "read_text_file":        "filesystem_read",
    "search_text":           "filesystem_read",
    # Filesystem write tools
    "write_text_file":       "filesystem_write",
    # MCP memory
    "mcp_memory_call":       "mcp_memory",
    # MCP sequential thinking
    "mcp_sequential_thinking": "mcp_sequential_thinking",
    # MCP context7
    "mcp_context7_call":     "mcp_context7",
    # MCP custom / generic call tools
    "mcp_call_tool":         "mcp_custom",
    "mcp_list_servers":      "mcp_custom",
    "mcp_list_server_tools": "mcp_custom",
}


def filter_tool_manifest_by_profile(
    tool_manifest: Iterable[Dict[str, str]],
    run_profile: "RunProfile",
) -> List[Dict[str, str]]:
    """Return the subset of *tool_manifest* permitted by *run_profile*.

    Each tool is looked up in ``_TOOL_PROFILE_FLAG`` to find the
    ``ToolAccess`` flag that governs its inclusion.  If the flag is enabled on
    the profile the tool is kept; otherwise it is dropped.  Tools whose names
    are not in the mapping are excluded (safe-fail).

    Args:
        tool_manifest: Full list of ``{"name": ..., "description": ...}`` dicts
            as returned by ``ToolRegistry.tool_manifest()``.
        run_profile: The active ``RunProfile`` whose ``tool_access`` flags are
            applied as the inclusion gate.

    Returns:
        A filtered list containing only tools permitted by the profile.
    """
    access = run_profile.tool_access
    result: List[Dict[str, str]] = []
    for tool in tool_manifest:
        name = tool.get("name", "")
        flag = _TOOL_PROFILE_FLAG.get(name)
        if flag is not None and getattr(access, flag, False):
            result.append(tool)
    return result


# ---------------------------------------------------------------------------
# Conversation history extraction from ledger
# ---------------------------------------------------------------------------


def build_conversation_history(
    ledger: "SessionLedger",
) -> List[Dict[str, str]]:
    """Extract model-facing conversation history from *ledger*.

    Only ``USER_MESSAGE`` and ``ASSISTANT_MESSAGE`` ledger events are mapped to
    conversation turns.  All other event kinds — including model-visible
    evidence events (``USER_CONTEXT``, ``TOOL_INVOKED``, ``TOOL_RESULT``,
    ``MEMORY_READ``) and ops-only events — are excluded from the history list.

    Evidence events are surfaced via ``compile_context_from_ledger()`` as
    evidence items in the current-turn user message instead.

    Inclusion rules:
    - ``USER_MESSAGE`` → ``{"role": "user", "content": payload["content"]}``
    - ``ASSISTANT_MESSAGE`` → ``{"role": "assistant", "content": payload["content"]}``
    - Everything else → excluded.

    Args:
        ledger: The session ledger to read from.

    Returns:
        Ordered list of ``{"role": ..., "content": ...}`` dicts.
    """
    # Import here to avoid module-level circular import; prompting.py is a
    # low-level module and durable_state imports from turn_trace only.
    from .durable_state import LedgerEventKind

    _HISTORY_KIND_TO_ROLE = {
        LedgerEventKind.USER_MESSAGE: "user",
        LedgerEventKind.ASSISTANT_MESSAGE: "assistant",
    }

    messages: List[Dict[str, str]] = []
    for event in ledger.events():
        role = _HISTORY_KIND_TO_ROLE.get(event.kind)
        if role is not None:
            messages.append({"role": role, "content": event.payload.get("content", "")})
    return messages


# ---------------------------------------------------------------------------
# Context compiler entry point
# ---------------------------------------------------------------------------


def compile_context_from_ledger(
    ledger: "SessionLedger",
    run_profile: "RunProfile",
    user_prompt: str,
    *,
    tool_manifest: Optional[Iterable[Dict[str, str]]] = None,
    evidence_items: Optional[Iterable[Dict[str, str]]] = None,
    memory_evidence: Optional[Iterable[Dict[str, str]]] = None,
    broker_controls_tools: bool = False,
) -> List[Dict[str, str]]:
    """Compile the full model-facing messages list from ledger state.

    This is the primary context-compiler entry point for TASK-LAH-004.  It
    consumes ledger state, a run profile, optional tools, and evidence from
    the current turn, then assembles the ``messages`` list that is sent to
    llama-server.

    Compiler inputs
    ~~~~~~~~~~~~~~~
    ledger
        Session ledger used to derive (a) the system prompt from the first
        ``SESSION_OPENED`` event and (b) the conversation history from
        ``USER_MESSAGE`` / ``ASSISTANT_MESSAGE`` events.
    run_profile
        Gates which tool categories are injected into the system manifest.
    user_prompt
        Current-turn question from the caller; placed in the final user
        message after the evidence block.
    tool_manifest
        Full broker tool list to be filtered by *run_profile* before
        injection.  ``None`` or empty → no tool block in system message.
    evidence_items
        Explicit evidence from deterministic tool calls this turn.
    memory_evidence
        Evidence retrieved from the memory subsystem this turn.
        Prepended before *evidence_items* in the evidence block.
    broker_controls_tools
        When ``True`` the system prompt uses the broker-in-control tool line.

    Compiler outputs
    ~~~~~~~~~~~~~~~~
    A ``List[Dict[str, str]]`` of chat messages:

    1. System message — persona + policy block + (optional) gated tool
       manifest.
    2. (optional) Alternating user / assistant history from prior turns.
    3. User message — evidence block + current *user_prompt*.

    Model-facing inclusion rules
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - Ops-only events are never present in the output.
    - ``ASSISTANT_THINKING`` is excluded even though it may be model-visible
      in some configurations; it must not create re-injection loops.
    - ``MEMORY_READ`` events that carry a non-empty ``result_summary`` are
      surfaced as evidence items, not as conversation turns.
    - The evidence block is always present in the final user message
      (the compiler boundary is never a pure transcript replay).

    Args:
        ledger: Session ledger for this conversation.
        run_profile: Active run profile (gates tool manifest inclusion).
        user_prompt: Current-turn user question.
        tool_manifest: Full tool list; filtered by profile before injection.
        evidence_items: Tool-result evidence for the current turn.
        memory_evidence: Memory-subsystem evidence for the current turn.
        broker_controls_tools: Broker-control mode flag for tool prompting.

    Returns:
        ``messages`` list ready for ``LlamaServerRuntime.chat()``.
    """
    from .durable_state import LedgerEventKind

    # ------------------------------------------------------------------
    # 1. Derive system prompt from the first SESSION_OPENED event.
    # ------------------------------------------------------------------
    system_prompt = "You are a precise local assistant."
    opened_events = ledger.events(kind=LedgerEventKind.SESSION_OPENED)
    if opened_events:
        system_prompt = opened_events[0].payload.get("system_prompt", system_prompt)

    # ------------------------------------------------------------------
    # 2. Gate tool manifest by profile.
    # ------------------------------------------------------------------
    raw_manifest = list(tool_manifest or [])
    gated_manifest = filter_tool_manifest_by_profile(raw_manifest, run_profile)

    # ------------------------------------------------------------------
    # 3. Build the system message.
    # ------------------------------------------------------------------
    system_content = build_system_prompt(
        system_prompt,
        tool_manifest=gated_manifest,
        broker_controls_tools=broker_controls_tools,
    )

    # ------------------------------------------------------------------
    # 4. Build conversation history from ledger (prior turns only).
    # ------------------------------------------------------------------
    history = build_conversation_history(ledger)

    # ------------------------------------------------------------------
    # 5. Collect MEMORY_READ result_summary values as evidence items.
    # ------------------------------------------------------------------
    ledger_memory_evidence: List[Dict[str, str]] = []
    for event in ledger.events(kind=LedgerEventKind.MEMORY_READ):
        summary = event.payload.get("result_summary", "").strip()
        if summary:
            ledger_memory_evidence.append(
                {
                    "source": "ledger:memory_read",
                    "kind": "mcp-tool-result",
                    "content": summary,
                }
            )

    # ------------------------------------------------------------------
    # 6. Merge evidence: ledger memory → caller memory → explicit items.
    # ------------------------------------------------------------------
    merged_evidence: List[Dict[str, str]] = (
        ledger_memory_evidence
        + list(memory_evidence or [])
        + list(evidence_items or [])
    )

    # ------------------------------------------------------------------
    # 7. Build the current-turn user message (evidence + task).
    # ------------------------------------------------------------------
    user_content = "\n\n".join([
        "Evidence:\n%s" % format_evidence(merged_evidence),
        "Task:\n%s" % user_prompt.strip(),
    ])

    # ------------------------------------------------------------------
    # 8. Assemble and return.
    # ------------------------------------------------------------------
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})
    return messages
