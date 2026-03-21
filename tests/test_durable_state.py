"""Deterministic tests for broker/durable_state.py and broker/session_store.py.

Covers the four areas requested in TASK-LAH-003 review:
1. LedgerEvent.to_dict() / from_dict() round-trip fidelity.
2. Canonical visibility mapping for all 16 LedgerEventKind values.
3. SessionLedger.to_jsonlines() / from_jsonlines() restart-safe ordering and
   reconstruction.
4. SessionStore.create() seeding a session_opened event and get_ledger()
   exposing the ledger to callers.
"""

import json

import pytest

from broker.durable_state import (
    LEDGER_EVENT_VISIBILITY,
    LedgerEvent,
    LedgerEventKind,
    SessionLedger,
    record_artifact_created,
    record_artifact_deleted,
    record_artifact_updated,
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
from broker.session_store import SessionStore
from broker.turn_trace import VisibilityFlags


# ---------------------------------------------------------------------------
# 1. LedgerEvent.to_dict() / from_dict() round-trip fidelity
# ---------------------------------------------------------------------------


class TestLedgerEventRoundTrip:
    """LedgerEvent serialises to a plain dict and deserialises back without loss."""

    def _make_event(self) -> LedgerEvent:
        return record_user_message(
            "sess-1", 0, content="Hello, world!", turn_index=0
        )

    def test_to_dict_keys(self):
        event = self._make_event()
        d = event.to_dict()
        assert set(d.keys()) == {
            "event_id",
            "session_id",
            "sequence",
            "kind",
            "payload",
            "timestamp_utc",
            "visibility",
        }

    def test_to_dict_primitive_values(self):
        event = self._make_event()
        d = event.to_dict()
        assert d["session_id"] == "sess-1"
        assert d["sequence"] == 0
        assert d["kind"] == LedgerEventKind.USER_MESSAGE.value
        assert d["payload"] == {"content": "Hello, world!", "turn_index": 0}

    def test_to_dict_visibility_is_plain_dict(self):
        event = self._make_event()
        vis = event.to_dict()["visibility"]
        assert isinstance(vis, dict)
        assert set(vis.keys()) == {"visible_to_model", "visible_to_user", "visible_to_ops"}

    def test_round_trip_identity(self):
        event = self._make_event()
        restored = LedgerEvent.from_dict(event.to_dict())
        assert restored.event_id == event.event_id
        assert restored.session_id == event.session_id
        assert restored.sequence == event.sequence
        assert restored.kind == event.kind
        assert restored.payload == event.payload
        assert restored.timestamp_utc == event.timestamp_utc
        assert restored.visibility.visible_to_model == event.visibility.visible_to_model
        assert restored.visibility.visible_to_user == event.visibility.visible_to_user
        assert restored.visibility.visible_to_ops == event.visibility.visible_to_ops

    def test_round_trip_is_json_serialisable(self):
        event = self._make_event()
        raw = json.dumps(event.to_dict())  # must not raise
        back = LedgerEvent.from_dict(json.loads(raw))
        assert back.event_id == event.event_id

    def test_from_dict_rejects_unknown_kind(self):
        d = self._make_event().to_dict()
        d["kind"] = "not_a_real_kind"
        with pytest.raises(ValueError):
            LedgerEvent.from_dict(d)

    def test_all_factory_helpers_round_trip(self):
        """Every record_*() helper serialises and deserialises without loss."""
        sid = "sess-rt"
        factories_and_events = [
            record_session_opened(sid, 0, system_prompt="sys"),
            record_session_closed(sid, 1, reason="done"),
            record_profile_applied(sid, 2, profile_name="default"),
            record_constraint_applied(sid, 3, description="no-pii"),
            record_user_message(sid, 4, content="hi", turn_index=0),
            record_user_context(sid, 5, content="ctx", source="env"),
            record_assistant_message(sid, 6, content="hello", turn_index=0),
            record_assistant_thinking(sid, 7, content="...", turn_index=0),
            record_tool_invoked(sid, 8, tool_name="search", arguments={"q": "x"}),
            record_tool_result(sid, 9, tool_name="search", result="ok"),
            record_memory_read(sid, 10, query="q"),
            record_memory_write(sid, 11, key="k"),
            record_memory_sync(sid, 12),
            record_artifact_created(sid, 13, artifact_id="a1", artifact_type="doc"),
            record_artifact_updated(sid, 14, artifact_id="a1", artifact_type="doc"),
            record_artifact_deleted(sid, 15, artifact_id="a1"),
        ]
        for event in factories_and_events:
            restored = LedgerEvent.from_dict(event.to_dict())
            assert restored.kind == event.kind
            assert restored.payload == event.payload


# ---------------------------------------------------------------------------
# 2. Canonical visibility mapping for all 16 LedgerEventKind values
# ---------------------------------------------------------------------------


class TestVisibilityMapping:
    """LEDGER_EVENT_VISIBILITY covers every kind and enforces ops-only defaults."""

    def test_all_kinds_are_mapped(self):
        all_kinds = set(LedgerEventKind)
        mapped_kinds = set(LEDGER_EVENT_VISIBILITY.keys())
        assert all_kinds == mapped_kinds, (
            f"Unmapped kinds: {all_kinds - mapped_kinds}"
        )

    def test_exactly_16_kinds(self):
        assert len(LedgerEventKind) == 16

    @pytest.mark.parametrize("kind", [
        LedgerEventKind.SESSION_OPENED,
        LedgerEventKind.SESSION_CLOSED,
        LedgerEventKind.PROFILE_APPLIED,
        LedgerEventKind.CONSTRAINT_APPLIED,
        LedgerEventKind.ASSISTANT_THINKING,
        LedgerEventKind.MEMORY_WRITE,
        LedgerEventKind.MEMORY_SYNC,
        LedgerEventKind.ARTIFACT_DELETED,
    ])
    def test_ops_only_kinds_are_not_model_visible(self, kind):
        vis = LEDGER_EVENT_VISIBILITY[kind]
        assert not vis.visible_to_model, f"{kind} should not be model-visible"
        assert not vis.visible_to_user, f"{kind} should not be user-visible"
        assert vis.visible_to_ops, f"{kind} should be ops-visible"

    @pytest.mark.parametrize("kind", [
        LedgerEventKind.USER_MESSAGE,
        LedgerEventKind.ASSISTANT_MESSAGE,
    ])
    def test_all_audience_kinds(self, kind):
        vis = LEDGER_EVENT_VISIBILITY[kind]
        assert vis.visible_to_model
        assert vis.visible_to_user
        assert vis.visible_to_ops

    @pytest.mark.parametrize("kind", [
        LedgerEventKind.USER_CONTEXT,
        LedgerEventKind.TOOL_INVOKED,
        LedgerEventKind.TOOL_RESULT,
        LedgerEventKind.MEMORY_READ,
    ])
    def test_evidence_kinds_are_model_visible_but_not_user_visible(self, kind):
        vis = LEDGER_EVENT_VISIBILITY[kind]
        assert vis.visible_to_model
        assert not vis.visible_to_user
        assert vis.visible_to_ops

    @pytest.mark.parametrize("kind", [
        LedgerEventKind.ARTIFACT_CREATED,
        LedgerEventKind.ARTIFACT_UPDATED,
    ])
    def test_artifact_kinds_are_user_and_ops_visible(self, kind):
        vis = LEDGER_EVENT_VISIBILITY[kind]
        assert not vis.visible_to_model
        assert vis.visible_to_user
        assert vis.visible_to_ops

    def test_visibility_values_are_visibility_flags_instances(self):
        for kind, vis in LEDGER_EVENT_VISIBILITY.items():
            assert isinstance(vis, VisibilityFlags), (
                f"{kind}: expected VisibilityFlags, got {type(vis)}"
            )

    def test_record_helpers_apply_canonical_visibility(self):
        """Factory helpers must apply the LEDGER_EVENT_VISIBILITY preset."""
        sid = "sess-vis"
        pairs = [
            (record_user_message(sid, 0, content="hi", turn_index=0),
             LedgerEventKind.USER_MESSAGE),
            (record_assistant_thinking(sid, 1, content="...", turn_index=0),
             LedgerEventKind.ASSISTANT_THINKING),
            (record_memory_sync(sid, 2),
             LedgerEventKind.MEMORY_SYNC),
        ]
        for event, kind in pairs:
            canonical = LEDGER_EVENT_VISIBILITY[kind]
            assert event.visibility.visible_to_model == canonical.visible_to_model
            assert event.visibility.visible_to_user == canonical.visible_to_user
            assert event.visibility.visible_to_ops == canonical.visible_to_ops


# ---------------------------------------------------------------------------
# 3. SessionLedger serialisation, ordering, and restart-safe reconstruction
# ---------------------------------------------------------------------------


class TestSessionLedgerJsonlines:
    """SessionLedger persists and reconstructs correctly via JSON-lines."""

    def _populated_ledger(self, session_id: str = "sess-jl") -> SessionLedger:
        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, ledger.next_sequence, system_prompt="sys"))
        ledger.record(record_user_message(session_id, ledger.next_sequence, content="Hello", turn_index=0))
        ledger.record(record_assistant_message(session_id, ledger.next_sequence, content="Hi", turn_index=0))
        ledger.record(record_memory_sync(session_id, ledger.next_sequence))
        return ledger

    def test_to_jsonlines_produces_one_line_per_event(self):
        ledger = self._populated_ledger()
        lines = [l for l in ledger.to_jsonlines().splitlines() if l.strip()]
        assert len(lines) == len(ledger.events())

    def test_to_jsonlines_each_line_is_valid_json(self):
        ledger = self._populated_ledger()
        for line in ledger.to_jsonlines().splitlines():
            obj = json.loads(line)  # must not raise
            assert "event_id" in obj

    def test_from_jsonlines_restores_event_count(self):
        ledger = self._populated_ledger()
        restored = SessionLedger.from_jsonlines(ledger.session_id, ledger.to_jsonlines())
        assert len(restored.events()) == len(ledger.events())

    def test_from_jsonlines_preserves_sequence_order(self):
        ledger = self._populated_ledger()
        restored = SessionLedger.from_jsonlines(ledger.session_id, ledger.to_jsonlines())
        sequences = [e.sequence for e in restored.events()]
        assert sequences == sorted(sequences)

    def test_from_jsonlines_reconstructs_correct_kinds(self):
        ledger = self._populated_ledger()
        restored = SessionLedger.from_jsonlines(ledger.session_id, ledger.to_jsonlines())
        original_kinds = [e.kind for e in ledger.events()]
        restored_kinds = [e.kind for e in restored.events()]
        assert original_kinds == restored_kinds

    def test_from_jsonlines_handles_out_of_order_lines(self):
        """Lines that arrive out-of-order are re-sorted by sequence."""
        session_id = "sess-oo"
        ledger = SessionLedger(session_id)
        ledger.record(record_user_message(session_id, 0, content="A", turn_index=0))
        ledger.record(record_user_message(session_id, 1, content="B", turn_index=1))
        ledger.record(record_user_message(session_id, 2, content="C", turn_index=2))

        lines = ledger.to_jsonlines().splitlines()
        # Reverse the line order to simulate out-of-order flush.
        shuffled = "\n".join(reversed(lines))
        restored = SessionLedger.from_jsonlines(session_id, shuffled)
        assert [e.sequence for e in restored.events()] == [0, 1, 2]

    def test_from_jsonlines_empty_string_returns_empty_ledger(self):
        restored = SessionLedger.from_jsonlines("sess-empty", "")
        assert restored.events() == []

    def test_round_trip_payload_fidelity(self):
        session_id = "sess-pl"
        ledger = SessionLedger(session_id)
        ledger.record(record_tool_invoked(session_id, 0, tool_name="grep", arguments={"pattern": "foo"}))
        restored = SessionLedger.from_jsonlines(session_id, ledger.to_jsonlines())
        assert restored.events()[0].payload["tool_name"] == "grep"
        assert restored.events()[0].payload["arguments"] == {"pattern": "foo"}

    def test_model_visible_events_filter(self):
        ledger = self._populated_ledger()
        model_events = ledger.model_visible_events()
        # user_message and assistant_message are model-visible; session_opened
        # and memory_sync are ops-only.
        model_kinds = {e.kind for e in model_events}
        assert LedgerEventKind.USER_MESSAGE in model_kinds
        assert LedgerEventKind.ASSISTANT_MESSAGE in model_kinds
        assert LedgerEventKind.SESSION_OPENED not in model_kinds
        assert LedgerEventKind.MEMORY_SYNC not in model_kinds

    def test_user_visible_events_filter(self):
        ledger = self._populated_ledger()
        user_events = ledger.user_visible_events()
        user_kinds = {e.kind for e in user_events}
        assert LedgerEventKind.USER_MESSAGE in user_kinds
        assert LedgerEventKind.ASSISTANT_MESSAGE in user_kinds
        assert LedgerEventKind.SESSION_OPENED not in user_kinds

    def test_record_rejects_wrong_session_id(self):
        ledger = SessionLedger("sess-A")
        event = record_user_message("sess-B", 0, content="hi", turn_index=0)
        with pytest.raises(ValueError, match="sess-B"):
            ledger.record(event)

    def test_next_sequence_increments(self):
        session_id = "sess-seq"
        ledger = SessionLedger(session_id)
        assert ledger.next_sequence == 0
        ledger.record(record_user_message(session_id, ledger.next_sequence, content="a", turn_index=0))
        assert ledger.next_sequence == 1
        ledger.record(record_assistant_message(session_id, ledger.next_sequence, content="b", turn_index=0))
        assert ledger.next_sequence == 2


# ---------------------------------------------------------------------------
# 4. SessionStore.create() and get_ledger()
# ---------------------------------------------------------------------------


class TestSessionStore:
    """SessionStore seeds a session_opened event and exposes the ledger."""

    def test_create_returns_session_with_session_id(self):
        store = SessionStore()
        session = store.create("System prompt.")
        assert session.session_id
        assert len(session.session_id) > 0

    def test_get_ledger_returns_ledger_for_known_session(self):
        store = SessionStore()
        session = store.create("System prompt.")
        ledger = store.get_ledger(session.session_id)
        assert ledger is not None

    def test_get_ledger_returns_none_for_unknown_session(self):
        store = SessionStore()
        assert store.get_ledger("nonexistent") is None

    def test_create_seeds_session_opened_event(self):
        store = SessionStore()
        session = store.create("System prompt.")
        ledger = store.get_ledger(session.session_id)
        opened_events = ledger.events(kind=LedgerEventKind.SESSION_OPENED)
        assert len(opened_events) == 1

    def test_seeded_event_contains_system_prompt(self):
        store = SessionStore()
        session = store.create("My system prompt.")
        ledger = store.get_ledger(session.session_id)
        opened = ledger.events(kind=LedgerEventKind.SESSION_OPENED)[0]
        assert opened.payload["system_prompt"] == "My system prompt."

    def test_seeded_event_has_correct_session_id(self):
        store = SessionStore()
        session = store.create("sys")
        ledger = store.get_ledger(session.session_id)
        opened = ledger.events(kind=LedgerEventKind.SESSION_OPENED)[0]
        assert opened.session_id == session.session_id

    def test_seeded_event_is_ops_only(self):
        """session_opened must be ops-only per visibility rules."""
        store = SessionStore()
        session = store.create("sys")
        ledger = store.get_ledger(session.session_id)
        opened = ledger.events(kind=LedgerEventKind.SESSION_OPENED)[0]
        assert not opened.visibility.visible_to_model
        assert not opened.visibility.visible_to_user
        assert opened.visibility.visible_to_ops

    def test_seeded_event_sequence_is_zero(self):
        store = SessionStore()
        session = store.create("sys")
        ledger = store.get_ledger(session.session_id)
        opened = ledger.events(kind=LedgerEventKind.SESSION_OPENED)[0]
        assert opened.sequence == 0

    def test_ledger_next_sequence_after_seed_is_one(self):
        store = SessionStore()
        session = store.create("sys")
        ledger = store.get_ledger(session.session_id)
        assert ledger.next_sequence == 1

    def test_multiple_sessions_have_independent_ledgers(self):
        store = SessionStore()
        s1 = store.create("prompt 1")
        s2 = store.create("prompt 2")
        l1 = store.get_ledger(s1.session_id)
        l2 = store.get_ledger(s2.session_id)
        assert l1 is not l2
        assert l1.session_id == s1.session_id
        assert l2.session_id == s2.session_id

    def test_system_prompt_is_stripped(self):
        store = SessionStore()
        session = store.create("  trimmed  ")
        assert session.system_prompt == "trimmed"

    def test_ledger_accepts_additional_events_after_seed(self):
        store = SessionStore()
        session = store.create("sys")
        ledger = store.get_ledger(session.session_id)
        ledger.record(
            record_user_message(
                session.session_id, ledger.next_sequence, content="hi", turn_index=0
            )
        )
        assert ledger.next_sequence == 2
        assert len(ledger.events()) == 2
