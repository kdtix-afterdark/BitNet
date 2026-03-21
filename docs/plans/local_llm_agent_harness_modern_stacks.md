# Local LLM Agent Harness — Modern Stacks

A plan for designing, implementing, and verifying the local LLM agent harness
that wraps the BitNet broker into a testable, observable, and extensible
pipeline.

---

## §1 — Overview and Goals

The harness gives automated agents and human operators a uniform way to drive
the BitNet broker through complete multi-turn conversations, collect structured
traces, and assert correctness without requiring a live GPU or a real model
download.

**Goals:**

1. Define a **shared contract** (`Event`, `TurnResult`, visibility metadata)
   that every adapter and consumer can depend on.
2. Provide a **thin driver layer** that issues requests to the broker HTTP API
   and maps raw JSON responses into typed `TurnResult` records.
3. Support **deterministic test execution** via a mock model backend so CI can
   run without hardware.
4. Expose **structured turn traces** as the primary artifact for both
   regression tests and ops observability.

---

## §2 — Scope

| In scope | Out of scope |
|---|---|
| Canonical `Event`, `TurnResult`, `VisibilityFlags` contract | Provider-specific transport fields (e.g. raw llama-server JSON) |
| Harness driver: `HarnessDriver` class | Multi-node or distributed execution |
| Mock broker backend for CI | GPU kernel benchmarking |
| Turn trace serialisation (JSON) | Long-term persistence / database storage |
| Acceptance tests for TASK-LAH-001 through TASK-LAH-005 | Load testing |

---

## §3 — Dependencies

- Python ≥ 3.10
- `broker` package (this repository)
- No new third-party runtime dependencies beyond those already in
  `requirements.txt`

---

## §4 — Task Breakdown

| Task | Title | Blocking |
|---|---|---|
| TASK-LAH-001 | Event, TurnResult, and visibility contracts | TASK-LAH-002 |
| TASK-LAH-002 | HarnessDriver: broker HTTP adapter | TASK-LAH-003 |
| TASK-LAH-003 | Mock broker backend for CI | TASK-LAH-004 |
| TASK-LAH-004 | Turn trace serialisation | TASK-LAH-005 |
| TASK-LAH-005 | Harness acceptance tests | — |

---

## §5 — Architectural Sketch

```
┌─────────────────────────────────────────────────────────────────┐
│                         HarnessDriver                           │
│  run_turn(prompt) → TurnResult                                  │
│  - POST /chat                                                   │
│  - map JSON → TurnResult                                        │
│  - attach Events                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────┐
│                         BrokerApp                               │
│  (broker/server.py)                                             │
│  routes: /chat  /artifacts/draft  /sessions  /tools/run         │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   LlamaRuntime       ToolRegistry         McpRegistry
   (optional)        (deterministic)     (stdio MCP)
```

---

## §6 — Canonical Contract

The canonical contract is implemented in `broker/turn_trace.py`.

### 6.1 Event

An `Event` captures one discrete occurrence within a turn.

| Field | Type | Required | Visibility |
|---|---|---|---|
| `event_id` | `str` | ✓ | ops |
| `session_id` | `str` | ✓ | ops |
| `turn_index` | `int` | ✓ | ops |
| `role` | `str` | ✓ | ops |
| `content` | `str` | ✓ | ops |
| `timestamp_utc` | `str` | ✓ | ops |
| `source` | `str \| None` | — | ops |
| `kind` | `str \| None` | — | ops |
| `visibility` | `VisibilityFlags` | — | — |
| `metadata` | `dict` | — | ops |

Canonical `role` values: `"user"`, `"assistant"`, `"tool"`, `"broker"`.

Canonical `kind` values: `"user-message"`, `"model-response"`,
`"tool-result"`, `"mcp-tool-result"`, `"broker-signal"`.

### 6.2 TurnResult

A `TurnResult` is the normalised output of one complete turn.

| Field | Type | Required | Visibility |
|---|---|---|---|
| `turn_id` | `str` | ✓ | ops |
| `session_id` | `str` | ✓ | ops |
| `prompt` | `str` | ✓ | model, user, ops |
| `response` | `str` | ✓ | model, user, ops |
| `model_invoked` | `bool` | ✓ | user, ops |
| `route_applied` | `bool` | ✓ | user, ops |
| `repair_applied` | `bool` | ✓ | user, ops |
| `route_reason` | `str \| None` | — | user, ops |
| `repair_reason` | `str \| None` | — | user, ops |
| `evidence` | `list[dict]` | — | model, ops |
| `route_operations` | `list[dict]` | — | ops |
| `events` | `list[Event]` | — | ops |
| `latency_ms` | `float \| None` | — | ops |

### 6.3 VisibilityFlags

Three boolean audience flags govern how each field is forwarded.

| Flag | Meaning |
|---|---|
| `visible_to_model` | Included in the prompt context sent to the LLM |
| `visible_to_user` | Present in the user-facing API response payload |
| `visible_to_ops` | Emitted to audit / observability logs |

Canonical presets (see `broker/turn_trace.py`):

| Preset constant | model | user | ops |
|---|---|---|---|
| `VISIBILITY_EVIDENCE` | ✓ | — | ✓ |
| `VISIBILITY_USER_ONLY` | — | ✓ | — |
| `VISIBILITY_ALL` | ✓ | ✓ | ✓ |
| `VISIBILITY_OPS_ONLY` | — | — | ✓ |

---

## §7 — Evidence Item Schema

Evidence items are `dict` values with three canonical keys:

| Key | Type | Description |
|---|---|---|
| `source` | `str` | Origin label, e.g. `"tool:read_text_file"`, `"mcp:memory:search_nodes"` |
| `kind` | `str` | Category, e.g. `"tool-result"`, `"mcp-tool-result"`, `"evidence"` |
| `content` | `str` | JSON-serialised payload |

---

## §8 — Non-Goals

- The harness does not replace the broker's own unit tests.
- The harness does not define how the model is loaded or quantised.
- The harness does not persist traces to a database.

---

## §9 — Risks

| Risk | Mitigation |
|---|---|
| Broker HTTP API changes | Contract is versioned via `broker/turn_trace.py`; adapters must map |
| MCP server unavailability | Mock backend provides deterministic responses without MCP |
| Latency variance in CI | `latency_ms` is optional; tests do not assert timing |

---

## §10 — Verification Criteria

| Criterion | How Verified |
|---|---|
| All required `Event` fields present | Static type check; unit test instantiates `Event` with only required fields |
| All required `TurnResult` fields present | Static type check; unit test instantiates `TurnResult` with only required fields |
| `VisibilityFlags` cover model, user, ops | Unit test asserts each preset constant |
| Field-level visibility table complete | Unit test checks `TURN_RESULT_VISIBILITY` keys match `TurnResult.__dataclass_fields__` |
| No provider-specific transport fields in contract | Code review; `turn_trace.py` import list has no llama/OpenAI SDK imports |
| Downstream tasks can import contract | `TASK-LAH-002` driver imports `TurnResult` from `broker.turn_trace` |

---

_Last updated: 2026-03-21_
_Owner: US-LAH-001_
