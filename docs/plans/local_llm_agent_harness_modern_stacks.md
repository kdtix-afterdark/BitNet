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

## §11 — Run Profile and Capability Matrix

The canonical run profile model is implemented in `broker/run_profile.py`.

### 11.1 Sub-policy dataclasses

Four composable dataclasses express profile behaviour without embedding
provider-specific names.

| Dataclass | Purpose |
|---|---|
| `SandboxPolicy` | Execution permissions: read / write / network / exec |
| `ToolAccess` | Which broker and MCP tool categories are enabled |
| `MemoryPolicy` | Memory-routing priority and auto-store behaviour |
| `ModelBudget` | Context window, max-new-tokens, and temperature |

### 11.2 RunProfile

A `RunProfile` binds the four sub-policies together with a `name`,
`description`, and `model_family` hint so that adapters can select a
concrete model without provider names appearing in planning artifacts.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Unique profile identifier (key in matrix) |
| `description` | `str` | Human-readable use-case summary |
| `model_family` | `str` | Coarse capacity tier: `"fast"`, `"balanced"`, `"high-capacity"` |
| `tool_access` | `ToolAccess` | Tool-category permissions |
| `memory_policy` | `MemoryPolicy` | Memory-routing configuration |
| `sandbox_policy` | `SandboxPolicy` | Execution permissions |
| `budget` | `ModelBudget` | Token and temperature budget |

### 11.3 Canonical capability matrix

| Profile | `model_family` | fs read | fs write | mcp memory | seq-thinking | ctx7 | mcp custom | memory routing | allow write | allow network | ctx | max tokens | temp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `default` | balanced | ✓ | — | — | — | — | — | model_first | — | — | 2 048 | 512 | 0.2 |
| `read_only` | fast | ✓ | — | — | — | — | — | model_first | — | — | 2 048 | 256 | 0.1 |
| `memory_first` | balanced | ✓ | — | ✓ | — | — | — | memory_first | ✓ | — | 4 096 | 512 | 0.2 |
| `tool_heavy` | high-capacity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | memory_first | ✓ | ✓ | 8 192 | 1 024 | 0.3 |
| `thinking` | high-capacity | ✓ | — | — | ✓ | — | — | model_first | — | — | 8 192 | 2 048 | 0.4 |

### 11.4 Usage

```python
from broker.run_profile import resolve_profile

profile = resolve_profile("memory_first")
if profile.memory_policy.enabled:
    # activate memory routing …
    pass
```

Adapters that do not recognise a requested profile name receive the
`"default"` profile as a safe fallback via `resolve_profile()`.

---

## §12 — Session Ledger Event Model

The session ledger model is implemented in `broker/durable_state.py`.

### 12.1 Event-kind taxonomy

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
| Memory | `memory_read` | A memory-store query |
| Memory | `memory_write` | A memory-store write |
| Memory | `memory_sync` | A memory-store synchronisation checkpoint |
| Artifact | `artifact_created` | A draft artifact was created |
| Artifact | `artifact_updated` | A draft artifact was updated |
| Artifact | `artifact_deleted` | A draft artifact was deleted |

### 12.2 Visibility rules

| Kind | model | user | ops |
|---|---|---|---|
| `session_opened` | — | — | ✓ |
| `session_closed` | — | — | ✓ |
| `profile_applied` | — | — | ✓ |
| `constraint_applied` | — | — | ✓ |
| `user_message` | ✓ | ✓ | ✓ |
| `user_context` | ✓ | — | ✓ |
| `assistant_message` | ✓ | ✓ | ✓ |
| `assistant_thinking` | — | — | ✓ |
| `tool_invoked` | ✓ | — | ✓ |
| `tool_result` | ✓ | — | ✓ |
| `memory_read` | ✓ | — | ✓ |
| `memory_write` | — | — | ✓ |
| `memory_sync` | — | — | ✓ |
| `artifact_created` | — | ✓ | ✓ |
| `artifact_updated` | — | ✓ | ✓ |
| `artifact_deleted` | — | — | ✓ |

### 12.3 Restart-safe reconstruction

`SessionLedger` serialises all events to newline-delimited JSON via
`to_jsonlines()`.  `SessionLedger.from_jsonlines()` deserialises and re-sorts
by the monotone `sequence` counter to guarantee ordering on replay.

### 12.4 Usage

```python
from broker.durable_state import SessionLedger, record_user_message, record_assistant_message
from broker.session_store import SessionStore

store = SessionStore()
session = store.create(system_prompt="You are a helpful assistant.")
ledger = store.get_ledger(session.session_id)

# append events as the turn progresses
ledger.record(record_user_message(session.session_id, ledger.next_sequence,
                                  content="Hello", turn_index=0))
ledger.record(record_assistant_message(session.session_id, ledger.next_sequence,
                                       content="Hi!", turn_index=0))

# persist
jsonl = ledger.to_jsonlines()

# restore
restored = SessionLedger.from_jsonlines(session.session_id, jsonl)
```

---

_Last updated: 2026-03-21_
_Owner: US-LAH-001_
