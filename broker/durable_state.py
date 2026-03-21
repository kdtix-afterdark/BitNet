"""Append-only session ledger event model and visibility rules.

This module defines the event taxonomy for the durable session ledger.  Each
event class (encoded as a typed ``LedgerEventKind`` value) represents one
category of activity that can occur during a session.  Explicit visibility
rules are attached via ``LEDGER_EVENT_VISIBILITY`` so that consumers know
which audience – model, user, or ops – may observe each record.

The ledger is append-only: once written, events are never mutated or deleted.
This property, combined with the typed event taxonomy and the monotone
``sequence`` counter, enables restart-safe session reconstruction.

**Design constraints** (TASK-LAH-003):

- Do not conflate *ledger fidelity* (the full append-only audit record) with
  *model-facing replay fidelity* (the subset the model needs to regenerate
  coherent context).
- Keep ops-only data out of model-visible rules by default.  Consumers MUST
  filter on ``visibility.visible_to_model`` before injecting events into a
  prompt context.

Reference:
    docs/plans/artifacts/local_llm_agent_harness_modern_stacks/
    TASK-LAH-003_session_ledger_event_model_and_visibility_rules.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from broker.turn_trace import (
    VisibilityFlags,
    VISIBILITY_ALL,
    VISIBILITY_EVIDENCE,
    VISIBILITY_OPS_ONLY,
)


# ---------------------------------------------------------------------------
# Event-kind taxonomy
# ---------------------------------------------------------------------------


class LedgerEventKind(str, Enum):
    """Canonical taxonomy of session-ledger event types.

    Events are grouped into six classes:

    * **Policy** – session lifecycle and profile/constraint changes.
    * **User** – messages and context supplied by the human caller.
    * **Assistant** – responses and internal reasoning from the model.
    * **Tool** – invocations sent to broker/MCP tools and their results.
    * **Memory** – reads and writes to the memory store.
    * **Artifact** – draft-artifact creation, updates, and deletions.
    """

    # -- Policy ----------------------------------------------------------------
    SESSION_OPENED = "session_opened"
    SESSION_CLOSED = "session_closed"
    PROFILE_APPLIED = "profile_applied"
    CONSTRAINT_APPLIED = "constraint_applied"

    # -- User ------------------------------------------------------------------
    USER_MESSAGE = "user_message"
    USER_CONTEXT = "user_context"

    # -- Assistant -------------------------------------------------------------
    ASSISTANT_MESSAGE = "assistant_message"
    ASSISTANT_THINKING = "assistant_thinking"

    # -- Tool ------------------------------------------------------------------
    TOOL_INVOKED = "tool_invoked"
    TOOL_RESULT = "tool_result"

    # -- Memory ----------------------------------------------------------------
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    MEMORY_SYNC = "memory_sync"

    # -- Artifact --------------------------------------------------------------
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_DELETED = "artifact_deleted"


# ---------------------------------------------------------------------------
# Visibility rules per event kind
# ---------------------------------------------------------------------------

#: Maps each ``LedgerEventKind`` to its canonical ``VisibilityFlags``.
#: Consumers MUST respect these flags when forwarding ledger data to external
#: systems.  Ops-only events must never be injected into the model context.
LEDGER_EVENT_VISIBILITY: Dict[LedgerEventKind, VisibilityFlags] = {
    # Policy – ops audit only.  Models and users must not see internal session
    # lifecycle or policy-change records.
    LedgerEventKind.SESSION_OPENED:     VISIBILITY_OPS_ONLY,
    LedgerEventKind.SESSION_CLOSED:     VISIBILITY_OPS_ONLY,
    LedgerEventKind.PROFILE_APPLIED:    VISIBILITY_OPS_ONLY,
    LedgerEventKind.CONSTRAINT_APPLIED: VISIBILITY_OPS_ONLY,

    # User – messages are visible to all three audiences.  User context (e.g.
    # injected system facts) goes to the model and ops but not the user API.
    LedgerEventKind.USER_MESSAGE:       VISIBILITY_ALL,
    LedgerEventKind.USER_CONTEXT:       VISIBILITY_EVIDENCE,

    # Assistant – final messages are visible to all.  Internal thinking steps
    # are ops-only so they do not pollute the user response or create
    # re-injection loops in the model context.
    LedgerEventKind.ASSISTANT_MESSAGE:  VISIBILITY_ALL,
    LedgerEventKind.ASSISTANT_THINKING: VISIBILITY_OPS_ONLY,

    # Tool – invocations and results are forwarded to the model as evidence
    # (and captured for ops) but are not surfaced directly to users.
    LedgerEventKind.TOOL_INVOKED:       VISIBILITY_EVIDENCE,
    LedgerEventKind.TOOL_RESULT:        VISIBILITY_EVIDENCE,

    # Memory – reads are treated as evidence (model + ops).  Writes and sync
    # operations are ops-only: they carry no information the model needs to
    # resume conversation context.
    LedgerEventKind.MEMORY_READ:        VISIBILITY_EVIDENCE,
    LedgerEventKind.MEMORY_WRITE:       VISIBILITY_OPS_ONLY,
    LedgerEventKind.MEMORY_SYNC:        VISIBILITY_OPS_ONLY,

    # Artifact – create/update carry metadata the user cares about (user +
    # ops).  Deletes are ops-only; the artifact is gone so there is nothing
    # user-facing to surface.
    LedgerEventKind.ARTIFACT_CREATED:   VisibilityFlags(visible_to_user=True, visible_to_ops=True),
    LedgerEventKind.ARTIFACT_UPDATED:   VisibilityFlags(visible_to_user=True, visible_to_ops=True),
    LedgerEventKind.ARTIFACT_DELETED:   VISIBILITY_OPS_ONLY,
}


# ---------------------------------------------------------------------------
# LedgerEvent – a single append-only entry
# ---------------------------------------------------------------------------


@dataclass
class LedgerEvent:
    """A single append-only entry in the session ledger.

    Required fields
    ---------------
    event_id : str
        Globally unique identifier for this event (UUID recommended).
    session_id : str
        Identifier of the owning session.
    sequence : int
        Monotonically increasing counter within the session.  Used to
        guarantee ordered replay during restart-safe reconstruction.
    kind : LedgerEventKind
        Taxonomic category; also governs the default visibility preset.
    payload : dict
        Event-specific content.  Schema is defined per kind in the task
        artifact document.
    timestamp_utc : str
        ISO-8601 UTC timestamp at which this event was recorded.

    Optional fields
    ---------------
    visibility : VisibilityFlags
        Audience-visibility contract for this record.  Defaults to the
        canonical preset for the event kind as defined in
        ``LEDGER_EVENT_VISIBILITY``.
    """

    event_id: str
    session_id: str
    sequence: int
    kind: LedgerEventKind
    payload: Dict[str, Any]
    timestamp_utc: str
    visibility: VisibilityFlags = field(
        default_factory=lambda: VISIBILITY_OPS_ONLY
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-compatible dict for durable storage."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "kind": self.kind.value,
            "payload": self.payload,
            "timestamp_utc": self.timestamp_utc,
            "visibility": {
                "visible_to_model": self.visibility.visible_to_model,
                "visible_to_user": self.visibility.visible_to_user,
                "visible_to_ops": self.visibility.visible_to_ops,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LedgerEvent":
        """Deserialise from a dict produced by ``to_dict()``.

        Enables restart-safe reconstruction: replay the JSON-lines ledger
        to restore full session state without re-executing the broker.
        """
        vis_raw = data.get("visibility", {})
        return cls(
            event_id=data["event_id"],
            session_id=data["session_id"],
            sequence=data["sequence"],
            kind=LedgerEventKind(data["kind"]),
            payload=data.get("payload", {}),
            timestamp_utc=data["timestamp_utc"],
            visibility=VisibilityFlags(
                visible_to_model=vis_raw.get("visible_to_model", False),
                visible_to_user=vis_raw.get("visible_to_user", False),
                visible_to_ops=vis_raw.get("visible_to_ops", True),
            ),
        )


# ---------------------------------------------------------------------------
# Record helpers – typed factory functions, one per event kind
# ---------------------------------------------------------------------------


def _make_event(
    session_id: str,
    sequence: int,
    kind: LedgerEventKind,
    payload: Dict[str, Any],
) -> LedgerEvent:
    """Internal factory: create a ``LedgerEvent`` with canonical visibility."""
    return LedgerEvent(
        event_id=str(uuid4()),
        session_id=session_id,
        sequence=sequence,
        kind=kind,
        payload=payload,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        visibility=LEDGER_EVENT_VISIBILITY[kind],
    )


# -- Policy ------------------------------------------------------------------


def record_session_opened(
    session_id: str,
    sequence: int,
    *,
    system_prompt: str,
    profile: str = "default",
) -> LedgerEvent:
    """Record that a new session was opened."""
    return _make_event(
        session_id, sequence, LedgerEventKind.SESSION_OPENED,
        {"system_prompt": system_prompt, "profile": profile},
    )


def record_session_closed(
    session_id: str,
    sequence: int,
    *,
    reason: str = "",
) -> LedgerEvent:
    """Record that a session was closed."""
    return _make_event(
        session_id, sequence, LedgerEventKind.SESSION_CLOSED,
        {"reason": reason},
    )


def record_profile_applied(
    session_id: str,
    sequence: int,
    *,
    profile_name: str,
) -> LedgerEvent:
    """Record that a run profile was applied to the session."""
    return _make_event(
        session_id, sequence, LedgerEventKind.PROFILE_APPLIED,
        {"profile_name": profile_name},
    )


def record_constraint_applied(
    session_id: str,
    sequence: int,
    *,
    description: str,
) -> LedgerEvent:
    """Record that an operational constraint was applied."""
    return _make_event(
        session_id, sequence, LedgerEventKind.CONSTRAINT_APPLIED,
        {"description": description},
    )


# -- User --------------------------------------------------------------------


def record_user_message(
    session_id: str,
    sequence: int,
    *,
    content: str,
    turn_index: int,
) -> LedgerEvent:
    """Record a message submitted by the user."""
    return _make_event(
        session_id, sequence, LedgerEventKind.USER_MESSAGE,
        {"content": content, "turn_index": turn_index},
    )


def record_user_context(
    session_id: str,
    sequence: int,
    *,
    content: str,
    source: str = "",
) -> LedgerEvent:
    """Record contextual information injected from the user layer."""
    return _make_event(
        session_id, sequence, LedgerEventKind.USER_CONTEXT,
        {"content": content, "source": source},
    )


# -- Assistant ---------------------------------------------------------------


def record_assistant_message(
    session_id: str,
    sequence: int,
    *,
    content: str,
    turn_index: int,
) -> LedgerEvent:
    """Record a final response message produced by the model."""
    return _make_event(
        session_id, sequence, LedgerEventKind.ASSISTANT_MESSAGE,
        {"content": content, "turn_index": turn_index},
    )


def record_assistant_thinking(
    session_id: str,
    sequence: int,
    *,
    content: str,
    turn_index: int,
) -> LedgerEvent:
    """Record an internal reasoning/thinking step (ops-only)."""
    return _make_event(
        session_id, sequence, LedgerEventKind.ASSISTANT_THINKING,
        {"content": content, "turn_index": turn_index},
    )


# -- Tool --------------------------------------------------------------------


def record_tool_invoked(
    session_id: str,
    sequence: int,
    *,
    tool_name: str,
    arguments: Dict[str, Any],
) -> LedgerEvent:
    """Record that a tool was invoked."""
    return _make_event(
        session_id, sequence, LedgerEventKind.TOOL_INVOKED,
        {"tool_name": tool_name, "arguments": arguments},
    )


def record_tool_result(
    session_id: str,
    sequence: int,
    *,
    tool_name: str,
    result: str,
) -> LedgerEvent:
    """Record the result returned by a tool."""
    return _make_event(
        session_id, sequence, LedgerEventKind.TOOL_RESULT,
        {"tool_name": tool_name, "result": result},
    )


# -- Memory ------------------------------------------------------------------


def record_memory_read(
    session_id: str,
    sequence: int,
    *,
    query: str,
    result_summary: str = "",
) -> LedgerEvent:
    """Record a read from the memory store."""
    return _make_event(
        session_id, sequence, LedgerEventKind.MEMORY_READ,
        {"query": query, "result_summary": result_summary},
    )


def record_memory_write(
    session_id: str,
    sequence: int,
    *,
    key: str,
    summary: str = "",
) -> LedgerEvent:
    """Record a write to the memory store (ops-only)."""
    return _make_event(
        session_id, sequence, LedgerEventKind.MEMORY_WRITE,
        {"key": key, "summary": summary},
    )


def record_memory_sync(
    session_id: str,
    sequence: int,
    *,
    details: str = "",
) -> LedgerEvent:
    """Record a memory-store synchronisation checkpoint (ops-only)."""
    return _make_event(
        session_id, sequence, LedgerEventKind.MEMORY_SYNC,
        {"details": details},
    )


# -- Artifact ----------------------------------------------------------------


def record_artifact_created(
    session_id: str,
    sequence: int,
    *,
    artifact_id: str,
    artifact_type: str,
) -> LedgerEvent:
    """Record that a draft artifact was created."""
    return _make_event(
        session_id, sequence, LedgerEventKind.ARTIFACT_CREATED,
        {"artifact_id": artifact_id, "artifact_type": artifact_type},
    )


def record_artifact_updated(
    session_id: str,
    sequence: int,
    *,
    artifact_id: str,
    artifact_type: str,
) -> LedgerEvent:
    """Record that a draft artifact was updated."""
    return _make_event(
        session_id, sequence, LedgerEventKind.ARTIFACT_UPDATED,
        {"artifact_id": artifact_id, "artifact_type": artifact_type},
    )


def record_artifact_deleted(
    session_id: str,
    sequence: int,
    *,
    artifact_id: str,
    reason: str = "",
) -> LedgerEvent:
    """Record that a draft artifact was deleted (ops-only)."""
    return _make_event(
        session_id, sequence, LedgerEventKind.ARTIFACT_DELETED,
        {"artifact_id": artifact_id, "reason": reason},
    )


# ---------------------------------------------------------------------------
# SessionLedger – append-only event log for one session
# ---------------------------------------------------------------------------


class SessionLedger:
    """Append-only ordered log of ``LedgerEvent`` records for a single session.

    The ledger supports restart-safe reconstruction: all events can be
    serialised to JSON-lines format (one JSON object per line, ordered by
    ``sequence``).  On restart the ledger is replayed in sequence order to
    restore the full session history without re-executing the broker.

    Example::

        ledger = SessionLedger(session_id)
        ledger.record(record_session_opened(session_id, 0, system_prompt="…"))
        ledger.record(record_user_message(session_id, 1, content="hi", turn_index=0))

        # persist to durable storage
        jsonl = ledger.to_jsonlines()

        # restore from durable storage
        ledger2 = SessionLedger.from_jsonlines(session_id, jsonl)
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._events: List[LedgerEvent] = []

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def next_sequence(self) -> int:
        """Return the next available sequence number."""
        return len(self._events)

    def record(self, event: LedgerEvent) -> None:
        """Append an event to the ledger.

        Raises ``ValueError`` if the event belongs to a different session.
        Events are immutable once appended; the ledger is append-only.
        """
        if event.session_id != self._session_id:
            raise ValueError(
                f"Event session_id {event.session_id!r} does not match "
                f"ledger session_id {self._session_id!r}"
            )
        self._events.append(event)

    def events(
        self, *, kind: Optional[LedgerEventKind] = None
    ) -> List[LedgerEvent]:
        """Return an ordered snapshot of ledger events.

        Parameters
        ----------
        kind:
            When provided, only events of that kind are returned.
        """
        if kind is None:
            return list(self._events)
        return [e for e in self._events if e.kind == kind]

    def model_visible_events(self) -> List[LedgerEvent]:
        """Return events whose visibility permits inclusion in the model context."""
        return [e for e in self._events if e.visibility.visible_to_model]

    def user_visible_events(self) -> List[LedgerEvent]:
        """Return events that may be surfaced in the user-facing response."""
        return [e for e in self._events if e.visibility.visible_to_user]

    def to_jsonlines(self) -> str:
        """Serialise all events to JSON-lines for durable storage.

        Each line is a JSON object produced by ``LedgerEvent.to_dict()``.
        Lines are emitted in ``sequence`` order.
        """
        return "\n".join(json.dumps(e.to_dict()) for e in self._events)

    @classmethod
    def from_jsonlines(cls, session_id: str, data: str) -> "SessionLedger":
        """Reconstruct a ``SessionLedger`` from serialised JSON-lines.

        Enables restart-safe reconstruction: parse the persisted ledger and
        sort events by their ``sequence`` counter to guarantee ordering even
        if lines arrived out-of-order during a concurrent flush.
        """
        ledger = cls(session_id)
        parsed: List[LedgerEvent] = []
        for line in data.strip().splitlines():
            stripped = line.strip()
            if stripped:
                parsed.append(LedgerEvent.from_dict(json.loads(stripped)))
        parsed.sort(key=lambda e: e.sequence)
        for event in parsed:
            ledger._events.append(event)
        return ledger
