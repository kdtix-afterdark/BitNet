# TASK-LAH-003 — Session Ledger Event Model and Visibility Rules

_Imported from `docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-003_session_ledger_event_model_and_visibility_rules.md` on 2026-03-21._

## Summary

Map the append-only session ledger event model and visibility rules that the
compiler will consume.

---

## Status

**Complete.**

---

## Implementation

### New module: `broker/durable_state.py`

The session ledger model is implemented with four components.

#### `LedgerEventKind` — event taxonomy

Sixteen event kinds in six classes:

| Class | Kind | Description |
|---|---|---|
| Policy | `session_opened` | A new session was started |
| Policy | `session_closed` | A session was closed |
| Policy | `profile_applied` | A run profile was applied |
| Policy | `constraint_applied` | An operational constraint was applied |
| User | `user_message` | A message submitted by the human caller |
| User | `user_context` | Contextual information injected from the user layer |
| Assistant | `assistant_message` | A final response produced by the model |
| Assistant | `assistant_thinking` | An internal reasoning step |
| Tool | `tool_invoked` | A tool was called |
| Tool | `tool_result` | A tool returned a result |
| Memory | `memory_read` | A memory-store query was performed |
| Memory | `memory_write` | A memory-store write was performed |
| Memory | `memory_sync` | A memory-store synchronisation checkpoint |
| Artifact | `artifact_created` | A draft artifact was created |
| Artifact | `artifact_updated` | A draft artifact was updated |
| Artifact | `artifact_deleted` | A draft artifact was deleted |

#### `LEDGER_EVENT_VISIBILITY` — visibility rules per kind

| Kind | model | user | ops | Rationale |
|---|---|---|---|---|
| `session_opened` | — | — | ✓ | Internal lifecycle; never inject into model context |
| `session_closed` | — | — | ✓ | Internal lifecycle |
| `profile_applied` | — | — | ✓ | Policy metadata; ops audit only |
| `constraint_applied` | — | — | ✓ | Policy metadata; ops audit only |
| `user_message` | ✓ | ✓ | ✓ | Core turn content; visible to all |
| `user_context` | ✓ | — | ✓ | Injected facts; model + ops, not raw user-facing |
| `assistant_message` | ✓ | ✓ | ✓ | Core response; visible to all |
| `assistant_thinking` | — | — | ✓ | Internal reasoning; ops-only to avoid re-injection loops |
| `tool_invoked` | ✓ | — | ✓ | Evidence for model; not surfaced to user |
| `tool_result` | ✓ | — | ✓ | Evidence for model; not surfaced to user |
| `memory_read` | ✓ | — | ✓ | Memory evidence; model + ops |
| `memory_write` | — | — | ✓ | Storage op; no model or user value |
| `memory_sync` | — | — | ✓ | Storage checkpoint; ops-only |
| `artifact_created` | — | ✓ | ✓ | User-facing metadata update |
| `artifact_updated` | — | ✓ | ✓ | User-facing metadata update |
| `artifact_deleted` | — | — | ✓ | Artifact gone; ops-only tombstone |

#### `LedgerEvent` — append-only dataclass

| Field | Type | Required | Description |
|---|---|---|---|
| `event_id` | `str` | ✓ | Globally unique identifier (UUID) |
| `session_id` | `str` | ✓ | Owning session |
| `sequence` | `int` | ✓ | Monotone counter enabling ordered replay |
| `kind` | `LedgerEventKind` | ✓ | Event taxonomy category |
| `payload` | `dict` | ✓ | Kind-specific content |
| `timestamp_utc` | `str` | ✓ | ISO-8601 UTC creation timestamp |
| `visibility` | `VisibilityFlags` | — | Defaults to canonical preset for the kind |

Serialisation methods:

- `to_dict()` → JSON-compatible `dict`
- `from_dict(data)` → `LedgerEvent` (class method; enables reconstruction)

#### `record_*` factory helpers

One typed factory function per event kind.  Each function accepts the
session-scoped positional arguments (`session_id`, `sequence`) and
kind-specific keyword arguments, and returns a `LedgerEvent` with the
canonical visibility preset already applied.

| Helper | Kind |
|---|---|
| `record_session_opened` | `session_opened` |
| `record_session_closed` | `session_closed` |
| `record_profile_applied` | `profile_applied` |
| `record_constraint_applied` | `constraint_applied` |
| `record_user_message` | `user_message` |
| `record_user_context` | `user_context` |
| `record_assistant_message` | `assistant_message` |
| `record_assistant_thinking` | `assistant_thinking` |
| `record_tool_invoked` | `tool_invoked` |
| `record_tool_result` | `tool_result` |
| `record_memory_read` | `memory_read` |
| `record_memory_write` | `memory_write` |
| `record_memory_sync` | `memory_sync` |
| `record_artifact_created` | `artifact_created` |
| `record_artifact_updated` | `artifact_updated` |
| `record_artifact_deleted` | `artifact_deleted` |

#### `SessionLedger` — append-only log with restart-safe reconstruction

| Method / property | Description |
|---|---|
| `session_id` | Read-only session identifier |
| `next_sequence` | Next available sequence number |
| `record(event)` | Append an event (raises `ValueError` on session mismatch) |
| `events(*, kind=None)` | Ordered snapshot, optionally filtered by kind |
| `model_visible_events()` | Events with `visible_to_model=True` |
| `user_visible_events()` | Events with `visible_to_user=True` |
| `to_jsonlines()` | Serialise to newline-delimited JSON for durable storage |
| `from_jsonlines(session_id, data)` | Reconstruct from JSON-lines; re-sorts by `sequence` |

### Updated module: `broker/session_store.py`

`SessionStore` now:

- Maintains a `_ledgers` dict (`session_id → SessionLedger`) alongside `_sessions`.
- Calls `record_session_opened()` automatically when `create()` is called,
  seeding the ledger with the first policy event.
- Exposes `get_ledger(session_id) → Optional[SessionLedger]` so callers can
  append further events during a session's lifetime.

---

## Constraints Applied

- Ledger fidelity (full append-only audit) is **not** conflated with
  model-facing replay fidelity.  Consumers must filter on
  `visibility.visible_to_model` before injecting events into a prompt context.
- Ops-only event kinds (`session_opened`, `session_closed`, `profile_applied`,
  `constraint_applied`, `assistant_thinking`, `memory_write`, `memory_sync`,
  `artifact_deleted`) are excluded from model-visible rules by default.

---

## Verification

| Step | Action | Result |
|---|---|---|
| 1 | Review event list against policy/user/assistant/tool/memory/artifact taxonomy | All six classes covered with 16 kinds |
| 2 | Review `LEDGER_EVENT_VISIBILITY` against plan guidance | model/user/ops scopes are clear and consistent |
| 3 | Instantiate `LedgerEvent` with required fields only | No `TypeError` |
| 4 | Round-trip `LedgerEvent.to_dict()` / `from_dict()` | Values are preserved |
| 5 | `SessionLedger.from_jsonlines` round-trip | Reconstructed ledger matches original |
| 6 | `record_session_opened` session mismatch raises `ValueError` | Append-only invariant enforced |
| 7 | `SessionStore.create()` seeds a `session_opened` event | `get_ledger()` returns ledger with one policy event |

---

## Notes / Findings

- The `sequence` counter enables deterministic ordering during restart-safe
  reconstruction even if the backing store delivers lines out of order.
- `LedgerEvent.visibility` defaults to `VISIBILITY_OPS_ONLY` as a safe
  fallback if a record is constructed directly (not via a factory helper).
- The `payload` field is typed as `Dict[str, Any]` so that each event kind
  can carry structured data without requiring a separate dataclass per kind.
- The existing `Event` type in `broker/turn_trace.py` captures turn-level
  activity for the harness audit trail and is deliberately separate from the
  session-level `LedgerEvent`; the two types serve different consumers.

---

_Created: 2026-03-21_
_Assignee: @copilot_
_Parent Story: US-LAH-002_
