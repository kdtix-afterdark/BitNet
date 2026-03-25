"""Regression tests for broker/memory_routing.py.

Covers:
- _REMEMBER_RE matches both strict (entity: observation) and natural
  language (remember that <content>) forms.
- maybe_route_memory_prompt handles both forms correctly.
- Session disk persistence: save and reload.
- Profile-aware memory query: profile="memory_first" auto-populates memory_query.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Direct regex tests (fail fast if the pattern regressed)
# ---------------------------------------------------------------------------

class TestRememberRegex:
    """_REMEMBER_RE must match both strict and natural-language forms."""

    def _pattern(self):
        from broker.memory_routing import _REMEMBER_RE
        return _REMEMBER_RE

    def test_strict_form_entity_colon_observation(self):
        m = self._pattern().match("remember project: deadline is March 31")
        assert m is not None
        assert m.group("entity").strip() == "project"
        assert "March 31" in m.group("observation")

    def test_strict_form_case_insensitive(self):
        m = self._pattern().match("REMEMBER Alice: likes Python")
        assert m is not None
        assert "Alice" in m.group("entity")

    def test_natural_language_remember_that_form(self):
        m = self._pattern().match("Remember that the project deadline is March 31.")
        assert m is not None, "natural 'remember that ...' form must match"

    def test_natural_language_remember_that_lowercase(self):
        m = self._pattern().match("remember that alice likes python")
        assert m is not None

    def test_natural_language_without_that(self):
        """'remember the meeting is tomorrow' — no colon, no 'that'."""
        m = self._pattern().match("remember the meeting is tomorrow")
        assert m is not None

    def test_non_remember_prompt_does_not_match(self):
        m = self._pattern().match("What is the capital of France?")
        assert m is None

    def test_recall_prompt_does_not_match(self):
        m = self._pattern().match("recall the project notes")
        assert m is None


# ---------------------------------------------------------------------------
# maybe_route_memory_prompt: natural language remember form
# ---------------------------------------------------------------------------

class TestMaybeRouteMemoryPromptNaturalLanguage:
    """maybe_route_memory_prompt must route 'remember that ...' prompts."""

    def _make_mock_registry(self, create_result: Any = None, open_result: Any = None):
        registry = MagicMock()
        registry.call_tool.side_effect = lambda server, tool, args=None: (
            {"entities": []} if tool == "open_nodes"
            else (create_result or {"entities": [{"name": "memo"}]})
        )
        return registry

    def test_natural_remember_that_is_handled(self):
        from broker.memory_routing import maybe_route_memory_prompt
        registry = self._make_mock_registry()
        result = maybe_route_memory_prompt(
            "Remember that the project deadline is March 31.",
            registry,
        )
        assert result is not None
        assert result.handled is True

    def test_natural_remember_that_calls_create_entities(self):
        from broker.memory_routing import maybe_route_memory_prompt
        registry = self._make_mock_registry()
        maybe_route_memory_prompt(
            "Remember that the project deadline is March 31.",
            registry,
        )
        # Must have made at least one MCP call
        assert registry.call_tool.call_count >= 1

    def test_natural_remember_that_route_operations_present(self):
        from broker.memory_routing import maybe_route_memory_prompt
        registry = self._make_mock_registry()
        result = maybe_route_memory_prompt(
            "Remember that Alice likes Python.",
            registry,
        )
        assert result is not None
        assert result.operations
        tools_called = [op["tool"] for op in result.operations]
        assert any(t in ("create_entities", "add_observations") for t in tools_called)

    def test_strict_form_still_works(self):
        from broker.memory_routing import maybe_route_memory_prompt
        registry = self._make_mock_registry()
        result = maybe_route_memory_prompt("remember project: deadline March 31", registry)
        assert result is not None
        assert result.handled is True

    def test_non_memory_prompt_returns_none(self):
        from broker.memory_routing import maybe_route_memory_prompt
        registry = MagicMock()
        result = maybe_route_memory_prompt("What is 2 + 2?", registry)
        assert result is None
        registry.call_tool.assert_not_called()


# ---------------------------------------------------------------------------
# Session disk persistence
# ---------------------------------------------------------------------------

class TestSessionDiskPersistence:
    """Session messages must survive a SessionStore replacement (broker restart)."""

    def test_persist_and_reload_messages(self):
        from broker.session_store import persist_messages, load_persisted_session
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            messages = [
                {"role": "user", "content": "My name is Alice."},
                {"role": "assistant", "content": "Hello Alice!"},
            ]
            persist_messages(state_dir, "uat-1", messages, system_prompt="You are helpful.")
            loaded = load_persisted_session(state_dir, "uat-1")
            assert loaded is not None
            msgs, sys_prompt = loaded
            assert len(msgs) == 2
            assert msgs[0]["content"] == "My name is Alice."
            assert sys_prompt == "You are helpful."

    def test_load_nonexistent_session_returns_none(self):
        from broker.session_store import load_persisted_session
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_persisted_session(Path(tmpdir), "no-such-session")
            assert result is None

    def test_persist_creates_parent_dirs(self):
        from broker.session_store import persist_messages
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "deep" / "nested"
            persist_messages(state_dir, "s1", [{"role": "user", "content": "hi"}])
            assert (state_dir / "sessions" / "s1.json").exists()

    def test_overwrite_updates_messages(self):
        from broker.session_store import persist_messages, load_persisted_session
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            persist_messages(state_dir, "s1", [{"role": "user", "content": "first"}])
            persist_messages(state_dir, "s1", [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "second"},
            ])
            loaded = load_persisted_session(state_dir, "s1")
            assert loaded is not None
            msgs, _ = loaded
            assert len(msgs) == 2


# ---------------------------------------------------------------------------
# Profile-aware memory query
# ---------------------------------------------------------------------------

class TestProfileAwareMemoryQuery:
    """When profile='memory_first' and no explicit memory_query, the prompt
    should be used as the memory query for evidence collection."""

    def _make_registry_with_memory_result(self, entities=None):
        registry = MagicMock()
        result = {"entities": entities or [{"name": "memo", "observations": ["March 31"]}]}
        registry.call_tool.return_value = result
        return registry

    def test_memory_first_profile_triggers_evidence_collection(self):
        from broker.memory_routing import collect_memory_evidence_for_profile
        registry = self._make_registry_with_memory_result()
        result = collect_memory_evidence_for_profile(
            prompt="When is the project deadline?",
            profile="memory_first",
            mcp_registry=registry,
        )
        assert result is not None
        registry.call_tool.assert_called()

    def test_non_memory_profile_does_not_trigger(self):
        from broker.memory_routing import collect_memory_evidence_for_profile
        registry = MagicMock()
        result = collect_memory_evidence_for_profile(
            prompt="When is the project deadline?",
            profile="default",
            mcp_registry=registry,
        )
        assert result is None
        registry.call_tool.assert_not_called()

    def test_none_profile_does_not_trigger(self):
        from broker.memory_routing import collect_memory_evidence_for_profile
        registry = MagicMock()
        result = collect_memory_evidence_for_profile(
            prompt="What time is it?",
            profile=None,
            mcp_registry=registry,
        )
        assert result is None

    def test_explicit_memory_query_overrides_prompt(self):
        from broker.memory_routing import collect_memory_evidence_for_profile
        registry = self._make_registry_with_memory_result()
        result = collect_memory_evidence_for_profile(
            prompt="When is the project deadline?",
            profile="memory_first",
            mcp_registry=registry,
            explicit_query="project deadline",
        )
        # Should still call - explicit query triggers evidence collection
        assert result is not None
