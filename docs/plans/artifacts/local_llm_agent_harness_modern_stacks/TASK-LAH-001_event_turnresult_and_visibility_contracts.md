# TASK-LAH-001 — Event, TurnResult, and Visibility Contracts

_Imported from `docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-001_event_turnresult_and_visibility_contracts.md` on 2026-03-21._

## Summary

Define the first draft of canonical `Event`, `TurnResult`, and visibility metadata fields for the harness.

---

## Context

- **Parent Story AC**: Shared contract review and adapter readiness
- **Preceding Task**: None
- **Blocking Tasks**: `TASK-LAH-002`

---

## I Know I Am Done When

- [x] Required `Event` fields are listed.
- [x] `TurnResult` fields are listed.
- [x] Visibility flags are defined for model, user, and ops audiences.

---

## Implementation Notes

### Approach

The canonical fields were extracted from two sources:

1. **`broker/server.py`** — the `chat()` method returns a dict whose keys map
   directly onto `TurnResult` fields.  This is the primary runtime evidence.
2. **`broker/memory_routing.py`** — `MemoryRouteResult` fields (`handled`,
   `response`, `route_reason`, `evidence`, `operations`) informed the routing
   and evidence fields of `TurnResult`.
3. **`docs/plans/local_llm_agent_harness_modern_stacks.md` §6** — the plan
   document records the normalised field list and visibility table.

The contract was recorded as typed Python `dataclass` definitions in
`broker/turn_trace.py` so that downstream tasks can import and depend on it
directly.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Contract | `Event`, `TurnResult`, `VisibilityFlags` | `broker/turn_trace.py` | **Created by this task** |
| Plan | Harness architecture §6 | `docs/plans/local_llm_agent_harness_modern_stacks.md` | **Created by this task** |
| Runtime evidence | `BrokerApp.chat()` response dict | `broker/server.py` | Source of TurnResult fields |
| Runtime evidence | `MemoryRouteResult` | `broker/memory_routing.py` | Source of routing fields |

---

## Required `Event` Fields

| Field | Type | Description |
| --- | --- | --- |
| `event_id` | `str` | Globally unique identifier (UUID recommended) |
| `session_id` | `str` | Identifier of the parent session |
| `turn_index` | `int` | Zero-based position of the owning turn |
| `role` | `str` | Origin: `"user"`, `"assistant"`, `"tool"`, `"broker"` |
| `content` | `str` | Event payload (text or JSON-serialised tool result) |
| `timestamp_utc` | `str` | ISO-8601 UTC creation timestamp |

Optional `Event` fields: `source`, `kind`, `visibility`, `metadata`.

---

## `TurnResult` Fields

### Required

| Field | Type | Description |
| --- | --- | --- |
| `turn_id` | `str` | Globally unique turn identifier |
| `session_id` | `str` | Parent session identifier |
| `prompt` | `str` | Raw user input |
| `response` | `str` | Final response after routing and repair |
| `model_invoked` | `bool` | Whether the LLM was called |
| `route_applied` | `bool` | Whether a deterministic route intercepted the prompt |
| `repair_applied` | `bool` | Whether post-processing modified the model output |

### Optional

| Field | Type | Description |
| --- | --- | --- |
| `route_reason` | `str \| None` | Why a route was or was not taken |
| `repair_reason` | `str \| None` | Why repair was applied |
| `evidence` | `list[dict]` | Evidence items injected into model context |
| `route_operations` | `list[dict]` | Broker-executed operations (e.g. MCP memory writes) |
| `events` | `list[Event]` | Full audit trail of events in this turn |
| `latency_ms` | `float \| None` | Wall-clock ms for the complete turn |

---

## Visibility Flags

Three boolean flags on `VisibilityFlags` govern audience access:

| Flag | Audience | Meaning |
| --- | --- | --- |
| `visible_to_model` | Language model | Field is included in the prompt context |
| `visible_to_user` | End user / API caller | Field is present in the user-facing response |
| `visible_to_ops` | Operators / audit | Field is emitted to observability / audit logs |

### Canonical Presets

| Constant | model | user | ops | Used for |
| --- | --- | --- | --- | --- |
| `VISIBILITY_EVIDENCE` | ✓ | — | ✓ | Evidence items, tool results |
| `VISIBILITY_USER_ONLY` | — | ✓ | — | User-only fields (rare) |
| `VISIBILITY_ALL` | ✓ | ✓ | ✓ | Core prompt/response |
| `VISIBILITY_OPS_ONLY` | — | — | ✓ | Route ops, events, latency |

### Field-level Visibility for TurnResult

| Field | model | user | ops |
| --- | --- | --- | --- |
| `turn_id` | — | — | ✓ |
| `session_id` | — | — | ✓ |
| `prompt` | ✓ | ✓ | ✓ |
| `response` | ✓ | ✓ | ✓ |
| `model_invoked` | — | ✓ | ✓ |
| `route_applied` | — | ✓ | ✓ |
| `route_reason` | — | ✓ | ✓ |
| `repair_applied` | — | ✓ | ✓ |
| `repair_reason` | — | ✓ | ✓ |
| `evidence` | ✓ | — | ✓ |
| `route_operations` | — | — | ✓ |
| `events` | — | — | ✓ |
| `latency_ms` | — | — | ✓ |

---

## Constraints Applied

- No provider-specific transport fields (e.g. raw llama-server JSON keys such
  as `stop_reason`, `tokens_predicted`) are included in the canonical contract.
  These belong in the adapter layer only.
- The contract uses only Python standard-library types and the broker's own
  `dataclass` conventions.

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review field list against plan §1, §6, §10 | All canonical fields covered |
| 2 | Review against `broker/server.py` `chat()` response keys | Runtime evidence maps cleanly to TurnResult fields |
| 3 | Import `Event`, `TurnResult`, `VisibilityFlags` from `broker.turn_trace` | No import errors |
| 4 | Instantiate `TurnResult` with required fields only | No TypeError |
| 5 | Confirm `TURN_RESULT_VISIBILITY` keys match `TurnResult` field names | Complete coverage |

---

## Notes / Findings

- The broker's `chat()` response already contains all fields needed for
  `TurnResult`; the contract formalises what was implicit.
- `Event` fields align with the existing evidence item schema
  (`source`, `kind`, `content`) plus the session/turn context fields needed for
  a complete audit record.
- The `raw` field from `broker/server.py` (the raw llama-server JSON) is
  deliberately excluded from `TurnResult` as a provider-specific transport
  field; adapters may carry it separately.

---

_Created: 2026-03-21_
_Assignee: @copilot_
_Parent Story: US-LAH-001_
