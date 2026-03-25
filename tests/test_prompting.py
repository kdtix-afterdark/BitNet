"""Deterministic regression tests for broker/prompting.py.

Covers the four areas defined in TASK-LAH-004:
1. Existing prompt assembly helpers: format_evidence, format_tool_manifest,
   build_system_prompt, build_messages.
2. build_conversation_history() — extract model-visible turn history from a
   SessionLedger.
3. filter_tool_manifest_by_profile() — gate tools by RunProfile flags.
4. compile_context_from_ledger() — full context compiler entry point that
   consumes ledger state, run profile, tools, and memory evidence.

Regression scenarios protect these model-facing inclusion rules:
- Ops-only ledger events (session_opened, session_closed, profile_applied,
  constraint_applied, assistant_thinking, memory_write, memory_sync,
  artifact_deleted) MUST NOT appear in compiled model context.
- MEMORY_READ events are model-visible and appear as evidence items, not as
  conversation turns.
- The compiler boundary is NOT a pure transcript replay: the system policy
  block and evidence section are always present.
- Profile flags gate which tools appear in the manifest.
"""

from __future__ import annotations

import pytest

from broker.durable_state import (
    SessionLedger,
    record_assistant_message,
    record_assistant_thinking,
    record_constraint_applied,
    record_memory_read,
    record_memory_sync,
    record_memory_write,
    record_profile_applied,
    record_session_closed,
    record_session_opened,
    record_tool_invoked,
    record_tool_result,
    record_user_context,
    record_user_message,
)
from broker.prompting import (
    build_conversation_history,
    build_messages,
    build_system_prompt,
    compile_context_from_ledger,
    filter_tool_manifest_by_profile,
    format_evidence,
    format_tool_manifest,
)
from broker.run_profile import RunProfile, ToolAccess, MemoryPolicy, SandboxPolicy, ModelBudget


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _minimal_profile(
    *,
    filesystem_read: bool = True,
    filesystem_write: bool = False,
    mcp_memory: bool = False,
    mcp_sequential_thinking: bool = False,
    mcp_context7: bool = False,
    mcp_custom: bool = False,
) -> RunProfile:
    """Build a RunProfile with controlled tool flags for testing."""
    return RunProfile(
        name="test",
        description="Test profile",
        model_family="fast",
        tool_access=ToolAccess(
            filesystem_read=filesystem_read,
            filesystem_write=filesystem_write,
            mcp_memory=mcp_memory,
            mcp_sequential_thinking=mcp_sequential_thinking,
            mcp_context7=mcp_context7,
            mcp_custom=mcp_custom,
        ),
        memory_policy=MemoryPolicy(),
        sandbox_policy=SandboxPolicy(),
        budget=ModelBudget(),
    )


def _full_manifest() -> list:
    """Return a manifest covering all known broker tool categories."""
    return [
        {"name": "list_directory", "description": "List directory"},
        {"name": "read_text_file", "description": "Read file"},
        {"name": "search_text", "description": "Search text"},
        {"name": "mcp_memory_call", "description": "Memory call"},
        {"name": "mcp_sequential_thinking", "description": "Sequential thinking"},
        {"name": "mcp_context7_call", "description": "Context7 call"},
        {"name": "mcp_call_tool", "description": "MCP call tool"},
        {"name": "mcp_list_servers", "description": "List MCP servers"},
        {"name": "mcp_list_server_tools", "description": "List MCP server tools"},
    ]


def _populated_ledger(session_id: str = "sess-p") -> SessionLedger:
    """Ledger with one complete turn: user message + assistant response."""
    ledger = SessionLedger(session_id)
    ledger.record(
        record_session_opened(session_id, ledger.next_sequence, system_prompt="You are a test assistant.")
    )
    ledger.record(
        record_user_message(session_id, ledger.next_sequence, content="Hello!", turn_index=0)
    )
    ledger.record(
        record_assistant_message(session_id, ledger.next_sequence, content="Hi there!", turn_index=0)
    )
    return ledger


# ---------------------------------------------------------------------------
# 1. format_evidence
# ---------------------------------------------------------------------------


class TestFormatEvidence:
    """Regression tests for format_evidence()."""

    def test_empty_evidence_returns_no_evidence_message(self):
        assert format_evidence([]) == "No evidence was provided."

    def test_single_item_renders_source_and_kind(self):
        result = format_evidence([{"source": "tool:read", "kind": "tool-result", "content": "data"}])
        assert "[tool-result] tool:read" in result
        assert "data" in result

    def test_item_without_content_is_skipped(self):
        items = [
            {"source": "a", "kind": "k", "content": ""},
            {"source": "b", "kind": "k", "content": "real"},
        ]
        result = format_evidence(items)
        assert "real" in result
        assert "[k] a" not in result

    def test_multiple_items_separated_by_blank_lines(self):
        items = [
            {"source": "s1", "kind": "k", "content": "first"},
            {"source": "s2", "kind": "k", "content": "second"},
        ]
        result = format_evidence(items)
        assert "\n\n" in result
        assert "first" in result
        assert "second" in result

    def test_missing_source_falls_back_to_unknown(self):
        result = format_evidence([{"kind": "evidence", "content": "x"}])
        assert "unknown" in result

    def test_missing_kind_falls_back_to_evidence(self):
        result = format_evidence([{"source": "src", "content": "x"}])
        assert "[evidence] src" in result

    def test_all_empty_content_returns_no_evidence_message(self):
        items = [{"source": "a", "kind": "k", "content": "   "}]
        assert format_evidence(items) == "No evidence was provided."


# ---------------------------------------------------------------------------
# 2. format_tool_manifest
# ---------------------------------------------------------------------------


class TestFormatToolManifest:
    """Regression tests for format_tool_manifest()."""

    def test_empty_manifest_returns_empty_string(self):
        assert format_tool_manifest([], broker_controls_tools=False) == ""

    def test_single_tool_name_and_description_rendered(self):
        manifest = [{"name": "read_text_file", "description": "Read a file"}]
        result = format_tool_manifest(manifest, broker_controls_tools=False)
        assert "read_text_file" in result
        assert "Read a file" in result

    def test_broker_controls_tools_true_sets_control_line(self):
        manifest = [{"name": "t", "description": "d"}]
        result = format_tool_manifest(manifest, broker_controls_tools=True)
        assert "broker is in control" in result

    def test_broker_controls_tools_false_sets_not_in_control_line(self):
        manifest = [{"name": "t", "description": "d"}]
        result = format_tool_manifest(manifest, broker_controls_tools=False)
        assert "not in control" in result

    def test_usage_rules_section_always_present(self):
        manifest = [{"name": "t", "description": "d"}]
        result = format_tool_manifest(manifest, broker_controls_tools=False)
        assert "Tool usage rules" in result

    def test_multiple_tools_all_appear(self):
        manifest = [
            {"name": "alpha", "description": "Alpha tool"},
            {"name": "beta", "description": "Beta tool"},
        ]
        result = format_tool_manifest(manifest, broker_controls_tools=False)
        assert "alpha" in result
        assert "beta" in result


# ---------------------------------------------------------------------------
# 3. build_system_prompt
# ---------------------------------------------------------------------------


class TestBuildSystemPrompt:
    """Regression tests for build_system_prompt()."""

    def test_policy_block_contains_current_date(self):
        result = build_system_prompt("Base prompt.")
        # The policy block always includes a date; just verify the key phrase.
        assert "Current local date:" in result

    def test_base_prompt_included(self):
        result = build_system_prompt("My base prompt.")
        assert "My base prompt." in result

    def test_empty_base_prompt_uses_default(self):
        result = build_system_prompt("")
        assert "precise local assistant" in result

    def test_manifest_block_absent_when_no_tools(self):
        result = build_system_prompt("Base.", tool_manifest=[], broker_controls_tools=False)
        assert "Known broker tools" not in result

    def test_manifest_block_present_when_tools_provided(self):
        manifest = [{"name": "my_tool", "description": "My tool"}]
        result = build_system_prompt("Base.", tool_manifest=manifest)
        assert "my_tool" in result

    def test_operating_rules_always_present(self):
        result = build_system_prompt("x")
        assert "Operating rules:" in result


# ---------------------------------------------------------------------------
# 4. build_messages
# ---------------------------------------------------------------------------


class TestBuildMessages:
    """Regression tests for build_messages()."""

    def test_returns_exactly_two_messages(self):
        msgs = build_messages("sys", "hi", [])
        assert len(msgs) == 2

    def test_first_message_is_system_role(self):
        msgs = build_messages("sys", "hi", [])
        assert msgs[0]["role"] == "system"

    def test_second_message_is_user_role(self):
        msgs = build_messages("sys", "hi", [])
        assert msgs[1]["role"] == "user"

    def test_evidence_appears_in_user_message(self):
        evidence = [{"source": "s", "kind": "k", "content": "evidence content"}]
        msgs = build_messages("sys", "task", evidence)
        assert "evidence content" in msgs[1]["content"]

    def test_task_appears_in_user_message(self):
        msgs = build_messages("sys", "Do the thing", [])
        assert "Do the thing" in msgs[1]["content"]

    def test_required_sections_add_output_contract(self):
        msgs = build_messages("sys", "task", [], required_sections=["Overview", "Details"])
        user_content = msgs[1]["content"]
        assert "Required headings:" in user_content
        assert "Output contract:" in user_content
        assert "Overview" in user_content
        assert "Details" in user_content

    def test_no_required_sections_omits_output_contract(self):
        msgs = build_messages("sys", "task", [])
        assert "Output contract:" not in msgs[1]["content"]

    def test_tool_manifest_in_system_prompt_when_provided(self):
        manifest = [{"name": "my_tool", "description": "Does stuff"}]
        msgs = build_messages("sys", "task", [], tool_manifest=manifest)
        assert "my_tool" in msgs[0]["content"]

    def test_no_evidence_label_still_present(self):
        msgs = build_messages("sys", "task", [])
        assert "Evidence:" in msgs[1]["content"]


# ---------------------------------------------------------------------------
# 5. build_conversation_history
# ---------------------------------------------------------------------------


class TestBuildConversationHistory:
    """build_conversation_history() extracts model-visible turn history."""

    def test_empty_ledger_returns_empty_list(self):
        ledger = SessionLedger("sess-empty")
        assert build_conversation_history(ledger) == []

    def test_session_opened_excluded_from_history(self):
        session_id = "sess-so"
        ledger = SessionLedger(session_id)
        ledger.record(
            record_session_opened(session_id, 0, system_prompt="sys")
        )
        history = build_conversation_history(ledger)
        assert history == []

    def test_user_message_maps_to_user_role(self):
        session_id = "sess-um"
        ledger = SessionLedger(session_id)
        ledger.record(record_user_message(session_id, 0, content="Hello", turn_index=0))
        history = build_conversation_history(ledger)
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"

    def test_assistant_message_maps_to_assistant_role(self):
        session_id = "sess-am"
        ledger = SessionLedger(session_id)
        ledger.record(record_assistant_message(session_id, 0, content="Hi!", turn_index=0))
        history = build_conversation_history(ledger)
        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert history[0]["content"] == "Hi!"

    def test_assistant_thinking_excluded(self):
        session_id = "sess-at"
        ledger = SessionLedger(session_id)
        ledger.record(record_user_message(session_id, 0, content="Q", turn_index=0))
        ledger.record(
            record_assistant_thinking(session_id, 1, content="internal thought", turn_index=0)
        )
        ledger.record(record_assistant_message(session_id, 2, content="A", turn_index=0))
        history = build_conversation_history(ledger)
        contents = [m["content"] for m in history]
        assert "internal thought" not in contents
        assert "Q" in contents
        assert "A" in contents

    def test_session_closed_excluded(self):
        session_id = "sess-sc"
        ledger = SessionLedger(session_id)
        ledger.record(record_user_message(session_id, 0, content="Q", turn_index=0))
        ledger.record(record_session_closed(session_id, 1, reason="done"))
        history = build_conversation_history(ledger)
        assert len(history) == 1
        assert "done" not in history[0]["content"]

    def test_profile_applied_excluded(self):
        session_id = "sess-pa"
        ledger = SessionLedger(session_id)
        ledger.record(record_profile_applied(session_id, 0, profile_name="default"))
        ledger.record(record_user_message(session_id, 1, content="Hi", turn_index=0))
        history = build_conversation_history(ledger)
        roles = [m["role"] for m in history]
        assert "user" in roles
        # profile_applied is ops-only and must not appear
        for msg in history:
            assert "default" not in msg["content"]

    def test_constraint_applied_excluded(self):
        session_id = "sess-ca"
        ledger = SessionLedger(session_id)
        ledger.record(record_constraint_applied(session_id, 0, description="no-pii"))
        ledger.record(record_user_message(session_id, 1, content="Hi", turn_index=0))
        history = build_conversation_history(ledger)
        for msg in history:
            assert "no-pii" not in msg["content"]

    def test_memory_write_excluded(self):
        session_id = "sess-mw"
        ledger = SessionLedger(session_id)
        ledger.record(record_memory_write(session_id, 0, key="k1", summary="stored"))
        ledger.record(record_user_message(session_id, 1, content="Q", turn_index=0))
        history = build_conversation_history(ledger)
        for msg in history:
            assert "stored" not in msg["content"]

    def test_memory_sync_excluded(self):
        session_id = "sess-ms"
        ledger = SessionLedger(session_id)
        ledger.record(record_memory_sync(session_id, 0, details="checkpoint"))
        ledger.record(record_user_message(session_id, 1, content="Q", turn_index=0))
        history = build_conversation_history(ledger)
        for msg in history:
            assert "checkpoint" not in msg["content"]

    def test_memory_read_excluded_from_history(self):
        """MEMORY_READ events are model-visible evidence but not conversation turns."""
        session_id = "sess-mr"
        ledger = SessionLedger(session_id)
        ledger.record(record_memory_read(session_id, 0, query="recall x", result_summary="found x"))
        ledger.record(record_user_message(session_id, 1, content="Q", turn_index=0))
        history = build_conversation_history(ledger)
        # memory_read must not appear as a history turn
        roles = [m["role"] for m in history]
        assert "user" in roles
        assert len(history) == 1  # only the user message

    def test_turn_order_preserved(self):
        session_id = "sess-ord"
        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, 0, system_prompt="sys"))
        ledger.record(record_user_message(session_id, 1, content="First", turn_index=0))
        ledger.record(record_assistant_message(session_id, 2, content="First reply", turn_index=0))
        ledger.record(record_user_message(session_id, 3, content="Second", turn_index=1))
        ledger.record(record_assistant_message(session_id, 4, content="Second reply", turn_index=1))
        history = build_conversation_history(ledger)
        assert len(history) == 4
        assert history[0]["content"] == "First"
        assert history[1]["content"] == "First reply"
        assert history[2]["content"] == "Second"
        assert history[3]["content"] == "Second reply"

    def test_tool_invoked_excluded_from_history(self):
        """TOOL_INVOKED is model-visible evidence, not a conversation turn."""
        session_id = "sess-ti"
        ledger = SessionLedger(session_id)
        ledger.record(
            record_tool_invoked(session_id, 0, tool_name="search_text", arguments={"q": "x"})
        )
        ledger.record(record_user_message(session_id, 1, content="Q", turn_index=0))
        history = build_conversation_history(ledger)
        assert len(history) == 1
        assert history[0]["role"] == "user"

    def test_tool_result_excluded_from_history(self):
        """TOOL_RESULT is model-visible evidence, not a conversation turn."""
        session_id = "sess-tr"
        ledger = SessionLedger(session_id)
        ledger.record(
            record_tool_result(session_id, 0, tool_name="search_text", result="found")
        )
        ledger.record(record_user_message(session_id, 1, content="Q", turn_index=0))
        history = build_conversation_history(ledger)
        assert len(history) == 1

    def test_user_context_excluded_from_history(self):
        """USER_CONTEXT events are evidence for the model, not conversation turns."""
        session_id = "sess-uc"
        ledger = SessionLedger(session_id)
        ledger.record(
            record_user_context(session_id, 0, content="injected fact", source="env")
        )
        ledger.record(record_user_message(session_id, 1, content="Q", turn_index=0))
        history = build_conversation_history(ledger)
        assert len(history) == 1
        assert "injected fact" not in history[0]["content"]


# ---------------------------------------------------------------------------
# 6. filter_tool_manifest_by_profile
# ---------------------------------------------------------------------------


class TestFilterToolManifestByProfile:
    """filter_tool_manifest_by_profile() gates tools by RunProfile flags."""

    def test_filesystem_read_tools_included_when_flag_true(self):
        profile = _minimal_profile(filesystem_read=True)
        manifest = [{"name": "read_text_file", "description": "Read"}, {"name": "list_directory", "description": "List"}]
        result = filter_tool_manifest_by_profile(manifest, profile)
        names = [t["name"] for t in result]
        assert "read_text_file" in names
        assert "list_directory" in names

    def test_filesystem_read_tools_excluded_when_flag_false(self):
        profile = _minimal_profile(filesystem_read=False)
        manifest = [
            {"name": "read_text_file", "description": "Read"},
            {"name": "list_directory", "description": "List"},
            {"name": "search_text", "description": "Search"},
        ]
        result = filter_tool_manifest_by_profile(manifest, profile)
        names = [t["name"] for t in result]
        assert "read_text_file" not in names
        assert "list_directory" not in names
        assert "search_text" not in names

    def test_mcp_memory_tool_included_when_flag_true(self):
        profile = _minimal_profile(mcp_memory=True)
        manifest = [{"name": "mcp_memory_call", "description": "Memory"}]
        result = filter_tool_manifest_by_profile(manifest, profile)
        assert any(t["name"] == "mcp_memory_call" for t in result)

    def test_mcp_memory_tool_excluded_when_flag_false(self):
        profile = _minimal_profile(mcp_memory=False)
        manifest = [{"name": "mcp_memory_call", "description": "Memory"}]
        result = filter_tool_manifest_by_profile(manifest, profile)
        assert not any(t["name"] == "mcp_memory_call" for t in result)

    def test_mcp_sequential_thinking_included_when_flag_true(self):
        profile = _minimal_profile(mcp_sequential_thinking=True)
        manifest = [{"name": "mcp_sequential_thinking", "description": "Thinking"}]
        result = filter_tool_manifest_by_profile(manifest, profile)
        assert any(t["name"] == "mcp_sequential_thinking" for t in result)

    def test_mcp_sequential_thinking_excluded_when_flag_false(self):
        profile = _minimal_profile(mcp_sequential_thinking=False)
        manifest = [{"name": "mcp_sequential_thinking", "description": "Thinking"}]
        result = filter_tool_manifest_by_profile(manifest, profile)
        assert not any(t["name"] == "mcp_sequential_thinking" for t in result)

    def test_mcp_context7_included_when_flag_true(self):
        profile = _minimal_profile(mcp_context7=True)
        manifest = [{"name": "mcp_context7_call", "description": "Context7"}]
        result = filter_tool_manifest_by_profile(manifest, profile)
        assert any(t["name"] == "mcp_context7_call" for t in result)

    def test_mcp_context7_excluded_when_flag_false(self):
        profile = _minimal_profile(mcp_context7=False)
        manifest = [{"name": "mcp_context7_call", "description": "Context7"}]
        result = filter_tool_manifest_by_profile(manifest, profile)
        assert not any(t["name"] == "mcp_context7_call" for t in result)

    def test_mcp_custom_tools_included_when_flag_true(self):
        profile = _minimal_profile(mcp_custom=True)
        manifest = [
            {"name": "mcp_call_tool", "description": "MCP call"},
            {"name": "mcp_list_servers", "description": "List servers"},
            {"name": "mcp_list_server_tools", "description": "List tools"},
        ]
        result = filter_tool_manifest_by_profile(manifest, profile)
        names = [t["name"] for t in result]
        assert "mcp_call_tool" in names
        assert "mcp_list_servers" in names
        assert "mcp_list_server_tools" in names

    def test_mcp_custom_tools_excluded_when_flag_false(self):
        profile = _minimal_profile(mcp_custom=False)
        manifest = [
            {"name": "mcp_call_tool", "description": "MCP call"},
            {"name": "mcp_list_servers", "description": "List servers"},
        ]
        result = filter_tool_manifest_by_profile(manifest, profile)
        assert result == []

    def test_all_tools_excluded_when_all_flags_false(self):
        profile = _minimal_profile(
            filesystem_read=False,
            filesystem_write=False,
            mcp_memory=False,
            mcp_sequential_thinking=False,
            mcp_context7=False,
            mcp_custom=False,
        )
        result = filter_tool_manifest_by_profile(_full_manifest(), profile)
        assert result == []

    def test_empty_manifest_returns_empty_list(self):
        profile = _minimal_profile()
        assert filter_tool_manifest_by_profile([], profile) == []

    def test_read_only_profile_includes_only_read_tools(self):
        from broker.run_profile import resolve_profile
        profile = resolve_profile("read_only")
        manifest = _full_manifest()
        result = filter_tool_manifest_by_profile(manifest, profile)
        names = [t["name"] for t in result]
        # read_only enables filesystem_read only
        assert "read_text_file" in names
        assert "list_directory" in names
        assert "search_text" in names
        assert "mcp_memory_call" not in names
        assert "mcp_sequential_thinking" not in names

    def test_tool_heavy_profile_includes_all_tools(self):
        from broker.run_profile import resolve_profile
        profile = resolve_profile("tool_heavy")
        manifest = _full_manifest()
        result = filter_tool_manifest_by_profile(manifest, profile)
        names = [t["name"] for t in result]
        assert "read_text_file" in names
        assert "mcp_memory_call" in names
        assert "mcp_sequential_thinking" in names
        assert "mcp_context7_call" in names


# ---------------------------------------------------------------------------
# 7. compile_context_from_ledger
# ---------------------------------------------------------------------------


class TestCompileContextFromLedger:
    """compile_context_from_ledger() assembles the full model-facing payload."""

    def test_returns_list_of_dicts(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "New question")
        assert isinstance(result, list)
        assert all(isinstance(m, dict) for m in result)

    def test_first_message_is_system_role(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert result[0]["role"] == "system"

    def test_last_message_is_user_role(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "New question")
        assert result[-1]["role"] == "user"

    def test_system_prompt_extracted_from_session_opened_event(self):
        session_id = "sess-sys"
        ledger = SessionLedger(session_id)
        ledger.record(
            record_session_opened(session_id, 0, system_prompt="Custom assistant persona.")
        )
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert "Custom assistant persona." in result[0]["content"]

    def test_policy_block_always_in_system_message(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert "Operating rules:" in result[0]["content"]

    def test_prior_turn_user_message_in_history(self):
        ledger = _populated_ledger()  # has "Hello!" + "Hi there!"
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "New question")
        all_contents = [m["content"] for m in result]
        assert any("Hello!" in c for c in all_contents)

    def test_prior_turn_assistant_message_in_history(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "New question")
        all_contents = [m["content"] for m in result]
        assert any("Hi there!" in c for c in all_contents)

    def test_current_prompt_in_last_user_message(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Unique current question xyz")
        assert "Unique current question xyz" in result[-1]["content"]

    def test_evidence_items_appear_in_last_user_message(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        evidence = [{"source": "tool:grep", "kind": "tool-result", "content": "match found"}]
        result = compile_context_from_ledger(ledger, profile, "Q", evidence_items=evidence)
        assert "match found" in result[-1]["content"]

    def test_memory_evidence_appears_in_last_user_message(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        mem_ev = [{"source": "mcp:memory", "kind": "mcp-tool-result", "content": "recalled fact"}]
        result = compile_context_from_ledger(ledger, profile, "Q", memory_evidence=mem_ev)
        assert "recalled fact" in result[-1]["content"]

    def test_memory_evidence_merged_with_explicit_evidence(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        evidence = [{"source": "tool:grep", "kind": "tool-result", "content": "grep hit"}]
        mem_ev = [{"source": "mcp:memory", "kind": "mcp-tool-result", "content": "recalled fact"}]
        result = compile_context_from_ledger(
            ledger, profile, "Q", evidence_items=evidence, memory_evidence=mem_ev
        )
        last_content = result[-1]["content"]
        assert "grep hit" in last_content
        assert "recalled fact" in last_content

    def test_tool_manifest_absent_when_profile_disables_all_tools(self):
        session_id = "sess-nt"
        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, 0, system_prompt="sys"))
        profile = _minimal_profile(
            filesystem_read=False,
            filesystem_write=False,
            mcp_memory=False,
            mcp_sequential_thinking=False,
            mcp_context7=False,
            mcp_custom=False,
        )
        result = compile_context_from_ledger(
            ledger, profile, "Q", tool_manifest=_full_manifest()
        )
        assert "Known broker tools" not in result[0]["content"]

    def test_tool_manifest_present_when_profile_enables_tools(self):
        session_id = "sess-wt"
        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, 0, system_prompt="sys"))
        profile = _minimal_profile(filesystem_read=True)
        manifest = [{"name": "read_text_file", "description": "Read file"}]
        result = compile_context_from_ledger(
            ledger, profile, "Q", tool_manifest=manifest
        )
        assert "read_text_file" in result[0]["content"]

    def test_empty_ledger_produces_valid_messages(self):
        ledger = SessionLedger("sess-empty")
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Hello")
        assert len(result) >= 2
        assert result[0]["role"] == "system"
        assert result[-1]["role"] == "user"
        assert "Hello" in result[-1]["content"]

    def test_no_tool_manifest_arg_produces_no_tool_block(self):
        ledger = _populated_ledger()
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert "Known broker tools" not in result[0]["content"]


# ---------------------------------------------------------------------------
# 8. Model-facing inclusion rules (regression scenarios)
# ---------------------------------------------------------------------------


class TestModelFacingInclusionRules:
    """Regression: ops-only events must never contaminate the model context.

    These tests protect against re-introduction of transcript-only replay
    as the compiler boundary and against leaking ops-only data to the model.
    """

    _OPS_ONLY_CONTENT = "SENTINEL_OPS_ONLY_XYZ_42"

    def _ledger_with_ops_event(self, factory_fn) -> SessionLedger:
        """Return a ledger that has exactly one ops-only event."""
        sid = "sess-ops"
        ledger = SessionLedger(sid)
        ledger.record(factory_fn(sid, 0))
        return ledger

    def _sentinel_in_messages(self, messages: list) -> bool:
        return any(self._OPS_ONLY_CONTENT in m["content"] for m in messages)

    def test_session_opened_not_in_model_context(self):
        sid = "sess-so2"
        ledger = SessionLedger(sid)
        ledger.record(
            record_session_opened(sid, 0, system_prompt=self._OPS_ONLY_CONTENT)
        )
        profile = _minimal_profile()
        # The sentinel is the system_prompt in session_opened payload.
        # It SHOULD appear in the system message (as the prompt) but NOT as a
        # conversation turn. Verify it does not appear as a "user" or
        # "assistant" history message.
        result = compile_context_from_ledger(ledger, profile, "Q")
        history_only = [m for m in result if m["role"] in ("user", "assistant")]
        # Last user message is the current turn — exclude it too
        history_turns = history_only[:-1]
        for msg in history_turns:
            assert self._OPS_ONLY_CONTENT not in msg["content"]

    def test_session_closed_never_in_model_context(self):
        sid = "sess-sc2"
        ledger = SessionLedger(sid)
        ledger.record(record_session_closed(sid, 0, reason=self._OPS_ONLY_CONTENT))
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert not self._sentinel_in_messages(result)

    def test_profile_applied_never_in_model_context(self):
        sid = "sess-pa2"
        ledger = SessionLedger(sid)
        ledger.record(record_profile_applied(sid, 0, profile_name=self._OPS_ONLY_CONTENT))
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert not self._sentinel_in_messages(result)

    def test_constraint_applied_never_in_model_context(self):
        sid = "sess-ca2"
        ledger = SessionLedger(sid)
        ledger.record(record_constraint_applied(sid, 0, description=self._OPS_ONLY_CONTENT))
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert not self._sentinel_in_messages(result)

    def test_assistant_thinking_never_in_model_context(self):
        sid = "sess-at2"
        ledger = SessionLedger(sid)
        ledger.record(
            record_assistant_thinking(sid, 0, content=self._OPS_ONLY_CONTENT, turn_index=0)
        )
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert not self._sentinel_in_messages(result)

    def test_memory_write_never_in_model_context(self):
        sid = "sess-mw2"
        ledger = SessionLedger(sid)
        ledger.record(
            record_memory_write(sid, 0, key=self._OPS_ONLY_CONTENT, summary="stored")
        )
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert not self._sentinel_in_messages(result)

    def test_memory_sync_never_in_model_context(self):
        sid = "sess-ms2"
        ledger = SessionLedger(sid)
        ledger.record(
            record_memory_sync(sid, 0, details=self._OPS_ONLY_CONTENT)
        )
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Q")
        assert not self._sentinel_in_messages(result)

    def test_compiler_boundary_is_not_transcript_only(self):
        """Policy block and evidence section must always be present.

        A pure transcript replay would omit the system policy block and
        evidence section.  The compiler must include them unconditionally.
        """
        session_id = "sess-tro"
        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, 0, system_prompt="Base."))
        ledger.record(record_user_message(session_id, 1, content="Hi", turn_index=0))
        ledger.record(record_assistant_message(session_id, 2, content="Hello", turn_index=0))
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "New question")
        # System message must contain the policy block (not just the persona).
        assert "Operating rules:" in result[0]["content"]
        # Final user message must contain "Evidence:" (even if empty).
        assert "Evidence:" in result[-1]["content"]

    def test_memory_read_evidence_appears_in_current_turn(self):
        """MEMORY_READ events from the ledger should surface as evidence."""
        session_id = "sess-mre"
        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, 0, system_prompt="sys"))
        ledger.record(
            record_memory_read(
                session_id, 1, query="recall project", result_summary="project is X"
            )
        )
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "What is the project?")
        last_content = result[-1]["content"]
        assert "project is X" in last_content

    def test_all_ops_only_ledger_produces_valid_output(self):
        """A ledger containing only ops-only events must still produce valid messages."""
        session_id = "sess-aoo"
        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, 0, system_prompt="sys"))
        ledger.record(record_profile_applied(session_id, 1, profile_name="default"))
        ledger.record(record_memory_sync(session_id, 2, details=""))
        profile = _minimal_profile()
        result = compile_context_from_ledger(ledger, profile, "Hello")
        assert result[0]["role"] == "system"
        assert result[-1]["role"] == "user"
        assert "Hello" in result[-1]["content"]


# ---------------------------------------------------------------------------
# 9. build_messages conversation history (multi-turn retention)
# ---------------------------------------------------------------------------


class TestBuildMessagesConversationHistory:
    """Regression tests for multi-turn conversation history in build_messages()."""

    def test_conversation_history_injected_between_system_and_current_user(self):
        history = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Nice to meet you, Alice!"},
        ]
        msgs = build_messages("sys", "What is my name?", [], conversation_history=history)
        roles = [m["role"] for m in msgs]
        assert roles == ["system", "user", "assistant", "user"]

    def test_conversation_history_content_preserved(self):
        history = [
            {"role": "user", "content": "Remember X."},
            {"role": "assistant", "content": "I will remember X."},
        ]
        msgs = build_messages("sys", "What do you remember?", [], conversation_history=history)
        assert msgs[1]["content"] == "Remember X."
        assert msgs[2]["content"] == "I will remember X."

    def test_no_history_returns_two_messages(self):
        msgs = build_messages("sys", "hello", [], conversation_history=None)
        assert len(msgs) == 2

    def test_empty_history_returns_two_messages(self):
        msgs = build_messages("sys", "hello", [], conversation_history=[])
        assert len(msgs) == 2

    def test_invalid_roles_in_history_are_skipped(self):
        history = [
            {"role": "system", "content": "injected system message"},
            {"role": "user", "content": "valid user turn"},
            {"role": "assistant", "content": "valid assistant turn"},
        ]
        msgs = build_messages("sys", "hi", [], conversation_history=history)
        roles = [m["role"] for m in msgs]
        assert roles.count("system") == 1

    def test_current_user_message_is_last(self):
        history = [
            {"role": "user", "content": "first turn"},
            {"role": "assistant", "content": "first reply"},
        ]
        msgs = build_messages("sys", "second question", [], conversation_history=history)
        assert msgs[-1]["role"] == "user"
        assert "second question" in msgs[-1]["content"]

    def test_grounded_user_prompt_false_omits_evidence_block(self):
        msgs = build_messages("sys", "hello", [], grounded_user_prompt=False)
        assert msgs[-1]["content"] == "hello"
        assert "Evidence:" not in msgs[-1]["content"]
