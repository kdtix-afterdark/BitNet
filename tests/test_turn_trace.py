"""Deterministic tests for broker/turn_trace.py — TASK-LAH-001 TDD coverage.

Covers:
1. VisibilityFlags dataclass: construction, defaults, and mutability.
2. Module-level visibility presets: VISIBILITY_EVIDENCE, VISIBILITY_USER_ONLY,
   VISIBILITY_ALL, VISIBILITY_OPS_ONLY.
3. Event dataclass: required fields, optional-field defaults, visibility default.
4. TurnResult dataclass: required fields, optional-field defaults, list defaults.
5. TURN_RESULT_VISIBILITY: completeness (all TurnResult fields mapped), and
   correctness of per-field audience assignments.
"""

import pytest

from broker.turn_trace import (
    TURN_RESULT_VISIBILITY,
    VISIBILITY_ALL,
    VISIBILITY_EVIDENCE,
    VISIBILITY_OPS_ONLY,
    VISIBILITY_USER_ONLY,
    Event,
    TurnResult,
    VisibilityFlags,
)


# ---------------------------------------------------------------------------
# VisibilityFlags
# ---------------------------------------------------------------------------


class TestVisibilityFlags:
    """Unit tests for the VisibilityFlags dataclass."""

    def test_all_false_by_default(self):
        vf = VisibilityFlags()
        assert vf.visible_to_model is False
        assert vf.visible_to_user is False
        assert vf.visible_to_ops is False

    def test_explicit_construction(self):
        vf = VisibilityFlags(visible_to_model=True, visible_to_user=True, visible_to_ops=True)
        assert vf.visible_to_model is True
        assert vf.visible_to_user is True
        assert vf.visible_to_ops is True

    def test_partial_construction_model_only(self):
        vf = VisibilityFlags(visible_to_model=True)
        assert vf.visible_to_model is True
        assert vf.visible_to_user is False
        assert vf.visible_to_ops is False

    def test_partial_construction_user_only(self):
        vf = VisibilityFlags(visible_to_user=True)
        assert vf.visible_to_model is False
        assert vf.visible_to_user is True
        assert vf.visible_to_ops is False

    def test_partial_construction_ops_only(self):
        vf = VisibilityFlags(visible_to_ops=True)
        assert vf.visible_to_model is False
        assert vf.visible_to_user is False
        assert vf.visible_to_ops is True

    def test_equality(self):
        a = VisibilityFlags(visible_to_model=True, visible_to_ops=True)
        b = VisibilityFlags(visible_to_model=True, visible_to_ops=True)
        assert a == b

    def test_inequality(self):
        a = VisibilityFlags(visible_to_model=True)
        b = VisibilityFlags(visible_to_user=True)
        assert a != b

    def test_is_dataclass_instance(self):
        import dataclasses
        assert dataclasses.is_dataclass(VisibilityFlags())


# ---------------------------------------------------------------------------
# Canonical visibility presets
# ---------------------------------------------------------------------------


class TestVisibilityPresets:
    """Verify the four canonical VisibilityFlags presets match their contracts."""

    def test_visibility_evidence_model_and_ops(self):
        assert VISIBILITY_EVIDENCE.visible_to_model is True
        assert VISIBILITY_EVIDENCE.visible_to_user is False
        assert VISIBILITY_EVIDENCE.visible_to_ops is True

    def test_visibility_user_only(self):
        assert VISIBILITY_USER_ONLY.visible_to_model is False
        assert VISIBILITY_USER_ONLY.visible_to_user is True
        assert VISIBILITY_USER_ONLY.visible_to_ops is False

    def test_visibility_all(self):
        assert VISIBILITY_ALL.visible_to_model is True
        assert VISIBILITY_ALL.visible_to_user is True
        assert VISIBILITY_ALL.visible_to_ops is True

    def test_visibility_ops_only(self):
        assert VISIBILITY_OPS_ONLY.visible_to_model is False
        assert VISIBILITY_OPS_ONLY.visible_to_user is False
        assert VISIBILITY_OPS_ONLY.visible_to_ops is True

    def test_presets_are_visibility_flags_instances(self):
        for preset in (VISIBILITY_EVIDENCE, VISIBILITY_USER_ONLY, VISIBILITY_ALL, VISIBILITY_OPS_ONLY):
            assert isinstance(preset, VisibilityFlags)

    def test_presets_are_distinct(self):
        presets = [VISIBILITY_EVIDENCE, VISIBILITY_USER_ONLY, VISIBILITY_ALL, VISIBILITY_OPS_ONLY]
        for i, p in enumerate(presets):
            for j, q in enumerate(presets):
                if i != j:
                    assert p != q, f"preset[{i}] and preset[{j}] should be distinct"


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


class TestEvent:
    """Unit tests for the Event dataclass."""

    def _minimal_event(self, **overrides) -> Event:
        defaults = dict(
            event_id="evt-001",
            session_id="sess-abc",
            turn_index=0,
            role="user",
            content="hello",
            timestamp_utc="2026-03-21T00:00:00Z",
        )
        defaults.update(overrides)
        return Event(**defaults)

    def test_required_fields_stored(self):
        ev = self._minimal_event()
        assert ev.event_id == "evt-001"
        assert ev.session_id == "sess-abc"
        assert ev.turn_index == 0
        assert ev.role == "user"
        assert ev.content == "hello"
        assert ev.timestamp_utc == "2026-03-21T00:00:00Z"

    def test_source_defaults_to_none(self):
        ev = self._minimal_event()
        assert ev.source is None

    def test_kind_defaults_to_none(self):
        ev = self._minimal_event()
        assert ev.kind is None

    def test_visibility_defaults_to_ops_only(self):
        ev = self._minimal_event()
        assert ev.visibility == VISIBILITY_OPS_ONLY
        assert ev.visibility.visible_to_model is False
        assert ev.visibility.visible_to_ops is True

    def test_metadata_defaults_to_empty_dict(self):
        ev = self._minimal_event()
        assert ev.metadata == {}

    def test_metadata_not_shared_between_instances(self):
        ev1 = self._minimal_event()
        ev2 = self._minimal_event()
        ev1.metadata["key"] = "value"
        assert "key" not in ev2.metadata

    def test_optional_fields_set(self):
        ev = self._minimal_event(
            source="tool:read_text_file",
            kind="tool-result",
            visibility=VISIBILITY_EVIDENCE,
            metadata={"adapter": "local"},
        )
        assert ev.source == "tool:read_text_file"
        assert ev.kind == "tool-result"
        assert ev.visibility == VISIBILITY_EVIDENCE
        assert ev.metadata == {"adapter": "local"}

    def test_turn_index_zero(self):
        ev = self._minimal_event(turn_index=0)
        assert ev.turn_index == 0

    def test_turn_index_nonzero(self):
        ev = self._minimal_event(turn_index=5)
        assert ev.turn_index == 5

    def test_role_values(self):
        for role in ("user", "assistant", "tool", "broker"):
            ev = self._minimal_event(role=role)
            assert ev.role == role

    def test_is_dataclass_instance(self):
        import dataclasses
        assert dataclasses.is_dataclass(self._minimal_event())


# ---------------------------------------------------------------------------
# TurnResult
# ---------------------------------------------------------------------------


class TestTurnResult:
    """Unit tests for the TurnResult dataclass."""

    def _minimal_turn(self, **overrides) -> TurnResult:
        defaults = dict(
            turn_id="turn-001",
            session_id="sess-abc",
            prompt="What is 2+2?",
            response="4",
            model_invoked=True,
            route_applied=False,
            repair_applied=False,
        )
        defaults.update(overrides)
        return TurnResult(**defaults)

    def test_required_fields_stored(self):
        tr = self._minimal_turn()
        assert tr.turn_id == "turn-001"
        assert tr.session_id == "sess-abc"
        assert tr.prompt == "What is 2+2?"
        assert tr.response == "4"
        assert tr.model_invoked is True
        assert tr.route_applied is False
        assert tr.repair_applied is False

    def test_route_reason_defaults_to_none(self):
        tr = self._minimal_turn()
        assert tr.route_reason is None

    def test_repair_reason_defaults_to_none(self):
        tr = self._minimal_turn()
        assert tr.repair_reason is None

    def test_evidence_defaults_to_empty_list(self):
        tr = self._minimal_turn()
        assert tr.evidence == []

    def test_route_operations_defaults_to_empty_list(self):
        tr = self._minimal_turn()
        assert tr.route_operations == []

    def test_events_defaults_to_empty_list(self):
        tr = self._minimal_turn()
        assert tr.events == []

    def test_latency_ms_defaults_to_none(self):
        tr = self._minimal_turn()
        assert tr.latency_ms is None

    def test_mutable_list_fields_not_shared(self):
        tr1 = self._minimal_turn()
        tr2 = self._minimal_turn()
        tr1.evidence.append({"source": "x", "kind": "test", "content": "c"})
        assert tr2.evidence == []

    def test_events_list_not_shared(self):
        tr1 = self._minimal_turn()
        tr2 = self._minimal_turn()
        ev = Event(
            event_id="e1", session_id="s", turn_index=0,
            role="user", content="x", timestamp_utc="2026-01-01T00:00:00Z",
        )
        tr1.events.append(ev)
        assert tr2.events == []

    def test_optional_fields_set(self):
        tr = self._minimal_turn(
            route_reason="memory hit",
            repair_reason="malformed JSON",
            latency_ms=123.4,
        )
        assert tr.route_reason == "memory hit"
        assert tr.repair_reason == "malformed JSON"
        assert tr.latency_ms == 123.4

    def test_model_invoked_false(self):
        tr = self._minimal_turn(model_invoked=False)
        assert tr.model_invoked is False

    def test_route_applied_true(self):
        tr = self._minimal_turn(route_applied=True, route_reason="cached")
        assert tr.route_applied is True
        assert tr.route_reason == "cached"

    def test_repair_applied_true(self):
        tr = self._minimal_turn(repair_applied=True, repair_reason="section missing")
        assert tr.repair_applied is True
        assert tr.repair_reason == "section missing"

    def test_is_dataclass_instance(self):
        import dataclasses
        assert dataclasses.is_dataclass(self._minimal_turn())


# ---------------------------------------------------------------------------
# TURN_RESULT_VISIBILITY
# ---------------------------------------------------------------------------


class TestTurnResultVisibility:
    """Verify TURN_RESULT_VISIBILITY is complete and correct per contract."""

    # All TurnResult field names that must appear in the visibility table.
    EXPECTED_FIELDS = {
        "turn_id", "session_id", "prompt", "response",
        "model_invoked", "route_applied", "route_reason",
        "repair_applied", "repair_reason",
        "evidence", "route_operations", "events", "latency_ms",
    }

    def test_all_expected_fields_mapped(self):
        for field_name in self.EXPECTED_FIELDS:
            assert field_name in TURN_RESULT_VISIBILITY, (
                f"Field '{field_name}' missing from TURN_RESULT_VISIBILITY"
            )

    def test_no_extra_unknown_fields(self):
        for field_name in TURN_RESULT_VISIBILITY:
            assert field_name in self.EXPECTED_FIELDS, (
                f"Unexpected field '{field_name}' in TURN_RESULT_VISIBILITY"
            )

    def test_all_values_are_visibility_flags(self):
        for field_name, vf in TURN_RESULT_VISIBILITY.items():
            assert isinstance(vf, VisibilityFlags), (
                f"TURN_RESULT_VISIBILITY['{field_name}'] is not a VisibilityFlags"
            )

    # Core response fields — visible to model, user, and ops (VISIBILITY_ALL)
    def test_prompt_is_all(self):
        assert TURN_RESULT_VISIBILITY["prompt"] == VISIBILITY_ALL

    def test_response_is_all(self):
        assert TURN_RESULT_VISIBILITY["response"] == VISIBILITY_ALL

    # Decision flags — visible to user and ops; NOT model
    def test_model_invoked_not_visible_to_model(self):
        assert TURN_RESULT_VISIBILITY["model_invoked"].visible_to_model is False

    def test_model_invoked_visible_to_user(self):
        assert TURN_RESULT_VISIBILITY["model_invoked"].visible_to_user is True

    def test_model_invoked_visible_to_ops(self):
        assert TURN_RESULT_VISIBILITY["model_invoked"].visible_to_ops is True

    def test_route_applied_not_visible_to_model(self):
        assert TURN_RESULT_VISIBILITY["route_applied"].visible_to_model is False

    def test_route_reason_not_visible_to_model(self):
        assert TURN_RESULT_VISIBILITY["route_reason"].visible_to_model is False

    def test_repair_applied_not_visible_to_model(self):
        assert TURN_RESULT_VISIBILITY["repair_applied"].visible_to_model is False

    def test_repair_reason_not_visible_to_model(self):
        assert TURN_RESULT_VISIBILITY["repair_reason"].visible_to_model is False

    # Evidence — VISIBILITY_EVIDENCE (model + ops, not user)
    def test_evidence_is_evidence_preset(self):
        assert TURN_RESULT_VISIBILITY["evidence"] == VISIBILITY_EVIDENCE

    def test_evidence_visible_to_model(self):
        assert TURN_RESULT_VISIBILITY["evidence"].visible_to_model is True

    def test_evidence_not_visible_to_user(self):
        assert TURN_RESULT_VISIBILITY["evidence"].visible_to_user is False

    def test_evidence_visible_to_ops(self):
        assert TURN_RESULT_VISIBILITY["evidence"].visible_to_ops is True

    # Ops-only fields
    def test_route_operations_is_ops_only(self):
        assert TURN_RESULT_VISIBILITY["route_operations"] == VISIBILITY_OPS_ONLY

    def test_events_is_ops_only(self):
        assert TURN_RESULT_VISIBILITY["events"] == VISIBILITY_OPS_ONLY

    def test_latency_ms_is_ops_only(self):
        assert TURN_RESULT_VISIBILITY["latency_ms"] == VISIBILITY_OPS_ONLY

    def test_turn_id_not_visible_to_model_or_user(self):
        vf = TURN_RESULT_VISIBILITY["turn_id"]
        assert vf.visible_to_model is False
        assert vf.visible_to_user is False
        assert vf.visible_to_ops is True

    def test_session_id_not_visible_to_model_or_user(self):
        vf = TURN_RESULT_VISIBILITY["session_id"]
        assert vf.visible_to_model is False
        assert vf.visible_to_user is False
        assert vf.visible_to_ops is True
