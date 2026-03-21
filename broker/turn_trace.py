"""Canonical Event, TurnResult, and visibility contract types for the broker harness.

These dataclasses form the shared contract between the harness runtime, adapters,
and downstream consumers (model context, user-facing responses, ops/audit logs).
Provider-specific transport fields are deliberately excluded; they belong in
adapter layers only.

Reference: docs/plans/local_llm_agent_harness_modern_stacks.md §1, §6, §10
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Visibility contract
# ---------------------------------------------------------------------------


@dataclass
class VisibilityFlags:
    """Controls which audiences can observe a field or record.

    Attributes:
        visible_to_model: When True the value is included in the prompt context
            sent to the language model.
        visible_to_user: When True the value is surfaced in the user-facing
            response or API payload.
        visible_to_ops: When True the value is emitted to audit / ops logs for
            observability and debugging.
    """

    visible_to_model: bool = False
    visible_to_user: bool = False
    visible_to_ops: bool = False


# Shared canonical visibility presets used across Event and TurnResult fields.

# Shown to the model and captured for ops; never sent directly to the user.
VISIBILITY_EVIDENCE = VisibilityFlags(visible_to_model=True, visible_to_ops=True)

# Shown only to the user; not injected into the model context.
VISIBILITY_USER_ONLY = VisibilityFlags(visible_to_user=True)

# Shown to both user and model; also captured for ops.
VISIBILITY_ALL = VisibilityFlags(
    visible_to_model=True, visible_to_user=True, visible_to_ops=True
)

# Ops / audit only; hidden from model and user.
VISIBILITY_OPS_ONLY = VisibilityFlags(visible_to_ops=True)


# ---------------------------------------------------------------------------
# Event – a single discrete occurrence within a turn
# ---------------------------------------------------------------------------


@dataclass
class Event:
    """A single discrete occurrence within a conversation turn.

    An Event captures one unit of activity – a user message, a model response
    fragment, a tool invocation result, or a broker-generated signal.  A list
    of Events is attached to every TurnResult so that the full audit trail is
    available without re-processing the raw exchange.

    Required fields
    ---------------
    event_id : str
        Globally unique identifier for this event (UUID recommended).
    session_id : str
        Identifier of the parent session this event belongs to.
    turn_index : int
        Zero-based position of the owning turn within the session.
    role : str
        Origin of the event.  Canonical values: ``"user"``, ``"assistant"``,
        ``"tool"``, ``"broker"``.
    content : str
        Human-readable or structured payload of the event.  For tool results
        this is the JSON-serialised result string.
    timestamp_utc : str
        ISO-8601 UTC timestamp at which this event was created.

    Optional fields
    ---------------
    source : str or None
        Fine-grained origin label, e.g. ``"tool:read_text_file"`` or
        ``"mcp:memory:search_nodes"``.  Mirrors the *source* key used in
        broker evidence items.
    kind : str or None
        Category of event, e.g. ``"user-message"``, ``"model-response"``,
        ``"tool-result"``, ``"mcp-tool-result"``, ``"broker-signal"``.
    visibility : VisibilityFlags
        Audience-visibility contract for this event record.  Defaults to
        ``VISIBILITY_OPS_ONLY`` so events are captured for audit but not
        automatically re-injected into the model or surfaced to the user.
    metadata : dict
        Arbitrary key-value pairs for adapter-specific annotations that do not
        belong in the canonical contract.
    """

    event_id: str
    session_id: str
    turn_index: int
    role: str
    content: str
    timestamp_utc: str
    source: Optional[str] = None
    kind: Optional[str] = None
    visibility: VisibilityFlags = field(default_factory=lambda: VISIBILITY_OPS_ONLY)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# TurnResult – the normalised output of processing one full turn
# ---------------------------------------------------------------------------


@dataclass
class TurnResult:
    """Normalised output of processing one complete conversation turn.

    A TurnResult is produced by the broker after a prompt has been routed,
    grounded with evidence, sent to the model (or handled deterministically),
    and post-processed.  It is the primary record handed to upstream callers
    and downstream adapters.

    Required fields
    ---------------
    turn_id : str
        Globally unique identifier for this turn (UUID recommended).
    session_id : str
        Identifier of the parent session.
    prompt : str
        The raw user-supplied input that initiated this turn.
    response : str
        The final response text returned to the caller after all repairs and
        routing decisions have been applied.

    Decision / audit fields
    -----------------------
    model_invoked : bool
        True when the language model was called to produce the response.
        False when the broker answered deterministically (memory routing, etc.).
    route_applied : bool
        True when a deterministic broker route intercepted the prompt before
        the model was invoked.
    route_reason : str or None
        Human-readable explanation of why a route was or was not taken.
    repair_applied : bool
        True when post-processing modified the raw model output.
    repair_reason : str or None
        Human-readable explanation of why a repair was applied.

    Evidence / context fields
    -------------------------
    evidence : list of dict
        Evidence items that were injected into the model context.  Each item
        has the keys ``source`` (str), ``kind`` (str), and ``content`` (str).
        Visibility: ``VISIBILITY_EVIDENCE`` – present in model context and ops
        logs but not directly exposed in the user-facing response payload.
    route_operations : list of dict
        Broker-executed operations (e.g. MCP memory writes/reads) that were
        performed during routing or evidence collection.
        Visibility: ``VISIBILITY_OPS_ONLY``.

    Turn history
    ------------
    events : list of Event
        Ordered list of Events generated during this turn, providing a full
        audit trail.
        Visibility: ``VISIBILITY_OPS_ONLY``.

    Optional timing
    ---------------
    latency_ms : float or None
        Wall-clock milliseconds elapsed for the complete turn, if measured.
        Visibility: ``VISIBILITY_OPS_ONLY``.
    """

    turn_id: str
    session_id: str
    prompt: str
    response: str
    model_invoked: bool
    route_applied: bool
    repair_applied: bool
    route_reason: Optional[str] = None
    repair_reason: Optional[str] = None
    evidence: List[Dict[str, str]] = field(default_factory=list)
    route_operations: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    latency_ms: Optional[float] = None


# ---------------------------------------------------------------------------
# Field-level visibility reference table
# ---------------------------------------------------------------------------

#: Maps each canonical TurnResult field name to its VisibilityFlags.
#: Downstream adapters MUST respect these flags when serialising or forwarding
#: TurnResult data to external systems.
TURN_RESULT_VISIBILITY: Dict[str, VisibilityFlags] = {
    # Core response – shown to user; model already produced it; captured for ops.
    "turn_id":          VisibilityFlags(visible_to_ops=True),
    "session_id":       VisibilityFlags(visible_to_ops=True),
    "prompt":           VISIBILITY_ALL,
    "response":         VISIBILITY_ALL,
    # Decision flags – ops and user; NOT re-injected into the model context.
    "model_invoked":    VisibilityFlags(visible_to_user=True, visible_to_ops=True),
    "route_applied":    VisibilityFlags(visible_to_user=True, visible_to_ops=True),
    "route_reason":     VisibilityFlags(visible_to_user=True, visible_to_ops=True),
    "repair_applied":   VisibilityFlags(visible_to_user=True, visible_to_ops=True),
    "repair_reason":    VisibilityFlags(visible_to_user=True, visible_to_ops=True),
    # Evidence – injected into model context; captured for ops; not user-facing.
    "evidence":         VISIBILITY_EVIDENCE,
    # Route operations – ops audit only.
    "route_operations": VISIBILITY_OPS_ONLY,
    # Event trail – ops audit only.
    "events":           VISIBILITY_OPS_ONLY,
    # Timing – ops only.
    "latency_ms":       VISIBILITY_OPS_ONLY,
}
