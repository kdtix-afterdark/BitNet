# TASK-LAH-004 — Context Compiler Assembly and Regression Coverage

_Imported from `docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md` on 2026-03-21._

## Summary

Define the context compiler assembly flow and the regression checks needed to
keep model-facing payloads intentional.

---

## Status

**Complete.**

---

## Implementation

### Module: `broker/prompting.py` — additions

Three new public functions were added alongside the existing prompt-assembly
helpers.

---

### `filter_tool_manifest_by_profile(tool_manifest, run_profile)`

Gates the broker tool manifest by the active ``RunProfile``.

#### Inputs

| Parameter | Type | Description |
|---|---|---|
| `tool_manifest` | `Iterable[Dict[str, str]]` | Full broker tool list — `{"name": ..., "description": ...}` dicts as returned by `ToolRegistry.tool_manifest()` |
| `run_profile` | `RunProfile` | Active run profile whose `tool_access` flags are applied as the inclusion gate |

#### Output

`List[Dict[str, str]]` — filtered tool list containing only tools whose
`ToolAccess` flag is enabled on the profile.

#### Inclusion rules

| Tool name(s) | Profile flag |
|---|---|
| `list_directory`, `read_text_file`, `search_text` | `tool_access.filesystem_read` |
| `write_text_file` | `tool_access.filesystem_write` |
| `mcp_memory_call` | `tool_access.mcp_memory` |
| `mcp_sequential_thinking` | `tool_access.mcp_sequential_thinking` |
| `mcp_context7_call` | `tool_access.mcp_context7` |
| `mcp_call_tool`, `mcp_list_servers`, `mcp_list_server_tools` | `tool_access.mcp_custom` |
| _(any other tool name)_ | **excluded** (safe-fail) |

---

### `build_conversation_history(ledger)`

Extracts model-facing conversation history from a ``SessionLedger``.

#### Inputs

| Parameter | Type | Description |
|---|---|---|
| `ledger` | `SessionLedger` | Session ledger to read from |

#### Output

`List[Dict[str, str]]` — ordered list of `{"role": ..., "content": ...}` dicts
representing prior conversation turns.

#### Inclusion rules

| Event kind | Mapped to | Rationale |
|---|---|---|
| `USER_MESSAGE` | `{"role": "user", "content": payload["content"]}` | Core turn content visible to model |
| `ASSISTANT_MESSAGE` | `{"role": "assistant", "content": payload["content"]}` | Core response visible to model |
| `USER_CONTEXT` | _(excluded from history)_ | Evidence for model; surfaced via evidence block |
| `TOOL_INVOKED` | _(excluded from history)_ | Evidence for model; not a conversation turn |
| `TOOL_RESULT` | _(excluded from history)_ | Evidence for model; not a conversation turn |
| `MEMORY_READ` | _(excluded from history)_ | Evidence for model; `result_summary` surfaces via evidence block |
| All ops-only kinds | _(excluded)_ | `visible_to_model = False`; must never contaminate context |

`ASSISTANT_THINKING` is additionally excluded to prevent re-injection loops.

---

### `compile_context_from_ledger(ledger, run_profile, user_prompt, ...)`

Primary context-compiler entry point.  Assembles the complete model-facing
``messages`` list from ledger state.

#### Inputs

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ledger` | `SessionLedger` | ✓ | Session ledger; source of system prompt and conversation history |
| `run_profile` | `RunProfile` | ✓ | Gates tool manifest inclusion |
| `user_prompt` | `str` | ✓ | Current-turn question from the caller |
| `tool_manifest` | `Iterable[Dict[str, str]]` | — | Full broker tool list; filtered by profile |
| `evidence_items` | `Iterable[Dict[str, str]]` | — | Explicit evidence from deterministic tool calls |
| `memory_evidence` | `Iterable[Dict[str, str]]` | — | Evidence from the memory subsystem |
| `broker_controls_tools` | `bool` | — | Broker-control-mode flag for tool prompting |

#### Output

`List[Dict[str, str]]` — the ``messages`` list for ``LlamaServerRuntime.chat()``:

```
[
  {"role": "system",    "content": "<system prompt + policy + gated tool manifest>"},
  {"role": "user",      "content": "<prior turn 1 user message>"},       # optional
  {"role": "assistant", "content": "<prior turn 1 assistant message>"},  # optional
  …                                                                       # optional
  {"role": "user",      "content": "Evidence:\n…\n\nTask:\n<user_prompt>"},
]
```

#### Assembly steps

1. Extract `system_prompt` from the first `SESSION_OPENED` payload in the
   ledger, or fall back to `"You are a precise local assistant."`.
2. Filter `tool_manifest` through `filter_tool_manifest_by_profile()`.
3. Build the system message via `build_system_prompt()`.
4. Extract conversation history via `build_conversation_history()`.
5. Collect `MEMORY_READ` events whose `result_summary` is non-empty and
   convert them to evidence items (source `"ledger:memory_read"`).
6. Merge evidence in priority order:
   `ledger_memory_evidence` → `memory_evidence` → `evidence_items`.
7. Build the current-turn user message via `format_evidence()` + `user_prompt`.
8. Return `[system_msg] + history + [current_user_msg]`.

---

## Model-facing inclusion rules (normative)

These rules define what may and must not appear in the assembled payload.

| Rule | Description |
|---|---|
| **R1** | `SESSION_OPENED`, `SESSION_CLOSED`, `PROFILE_APPLIED`, `CONSTRAINT_APPLIED` are ops-only; never injected into the model context. |
| **R2** | `ASSISTANT_THINKING` is excluded unconditionally to prevent re-injection loops. |
| **R3** | `MEMORY_WRITE`, `MEMORY_SYNC` are ops-only; never injected. |
| **R4** | `ARTIFACT_DELETED` is ops-only; never injected. |
| **R5** | Only `USER_MESSAGE` and `ASSISTANT_MESSAGE` events become conversation-history turns. |
| **R6** | `USER_CONTEXT`, `TOOL_INVOKED`, `TOOL_RESULT`, `MEMORY_READ` are model-visible evidence, not conversation turns. |
| **R7** | `MEMORY_READ.result_summary` is converted to an evidence item in the current-turn user message. |
| **R8** | The compiler boundary is never a pure transcript replay: the system policy block and evidence section are always present. |
| **R9** | Tool manifest is always gated by the run profile; disabled categories produce no manifest block. |
| **R10** | Memory evidence is prepended before explicit evidence in the evidence block. |

---

## Regression coverage

The regression suite is in `tests/test_prompting.py` and is run by
`.github/workflows/test-prompting.yml`.

### Test classes and scenarios covered

| Class | Scenarios |
|---|---|
| `TestFormatEvidence` | Empty list → sentinel message; item format; empty-content skip; multi-item separator; missing-key fallbacks |
| `TestFormatToolManifest` | Empty manifest; single-tool render; broker-control-mode lines; usage-rules section; multi-tool |
| `TestBuildSystemPrompt` | Policy block; base prompt; default prompt; manifest present/absent; operating rules |
| `TestBuildMessages` | Two messages; roles; evidence; task; required sections / output contract; tool manifest in system |
| `TestBuildConversationHistory` | Empty ledger; session_opened/closed excluded; user/assistant roles; thinking excluded; profile/constraint/memory-write/sync excluded; memory_read excluded from turns; tool_invoked/result excluded; user_context excluded; turn ordering |
| `TestFilterToolManifestByProfile` | Each tool category flag on/off; all-false empty result; `read_only` profile; `tool_heavy` profile |
| `TestCompileContextFromLedger` | Return type; system/user roles; system prompt from ledger; policy block always present; prior-turn history; current prompt; evidence/memory evidence merging; profile-gated tool manifest; empty ledger |
| `TestModelFacingInclusionRules` | **R1–R8** sentinel regressions; transcript-replay boundary guard; memory_read evidence surfaced; all-ops-only ledger |

### Regression scenarios protecting model-facing behaviour (not only storage)

| Scenario | What it protects |
|---|---|
| `test_session_opened_not_in_model_context` | R1 — lifecycle events do not become conversation turns |
| `test_session_closed_never_in_model_context` | R1 |
| `test_profile_applied_never_in_model_context` | R1 |
| `test_constraint_applied_never_in_model_context` | R1 |
| `test_assistant_thinking_never_in_model_context` | R2 — thinking steps cannot re-inject |
| `test_memory_write_never_in_model_context` | R3 |
| `test_memory_sync_never_in_model_context` | R3 |
| `test_compiler_boundary_is_not_transcript_only` | R8 — policy block + evidence always present |
| `test_memory_read_evidence_appears_in_current_turn` | R7 — memory recall surfaces as evidence |
| `test_all_ops_only_ledger_produces_valid_output` | R8 + compiler robustness |
| `test_tool_manifest_absent_when_profile_disables_all_tools` | R9 |
| `test_tool_manifest_present_when_profile_enables_tools` | R9 |
| `test_read_only_profile_includes_only_read_tools` | R9 — profile-level tool gating |
| `test_tool_heavy_profile_includes_all_tools` | R9 |

---

## GitHub CI versus local Apple Silicon + Metal UAT

### Covered by `.github/workflows/test-prompting.yml` (GitHub-hosted runners)

- All 82 tests in `tests/test_prompting.py` (TASK-LAH-004)
- All 51 tests in `tests/test_durable_state.py` (TASK-LAH-003)
- Triggered on push and pull request when relevant source files change

### Requires local Apple Silicon + Metal UAT (not covered by GitHub CI)

| Scenario | Why GitHub CI cannot cover it |
|---|---|
| End-to-end `/chat` round-trip: `compile_context_from_ledger()` → `LlamaServerRuntime.chat()` → repair pipeline | Requires a live GGUF model loaded via llama-server with Metal acceleration |
| Token-budget enforcement (`ctx_size`, `max_new_tokens`) under real generation | Requires the live model and GPU/Metal backend |
| Multi-turn session continuity across HTTP restart boundaries | Requires a running broker process and the model backend |
| Memory MCP server integration with real Knowledge Graph data | Requires a running memory MCP server process |
| Temperature and sampling behaviour validation | Requires live model generation |

---

## Constraints applied

- Transcript-only replay was not introduced as the compiler boundary: the
  system policy block and evidence section are present in every compiled
  payload (rule R8).
- Regression checks are focused on model-facing behaviour: every
  `TestModelFacingInclusionRules` test asserts what appears in the compiled
  messages list, not in storage or ledger serialisation.

---

## Verification

| Step | Action | Result |
|---|---|---|
| 1 | Review compiler path against harness plan | Inputs and outputs align: ledger, profile, tools, memory, and evidence all consumed |
| 2 | Review expected regression scenarios | Replay and prompt-shaping risks covered by `TestModelFacingInclusionRules` |
| 3 | Run `python3 -m pytest tests/test_prompting.py -v` | 82 tests pass |
| 4 | Run `python3 -m pytest tests/ -v` | 133 tests pass (no regressions) |
| 5 | Check `.github/workflows/test-prompting.yml` triggers | Workflow file present; triggers on push and PR for relevant paths |

---

## Notes / Findings

- `build_conversation_history()` deliberately excludes `USER_CONTEXT`,
  `TOOL_INVOKED`, `TOOL_RESULT`, and `MEMORY_READ` events from conversation
  turns.  These are model-visible but belong in the evidence block of the
  current turn, not in the alternating user/assistant history.  This
  separation prevents evidence pollution across turns.
- `_TOOL_PROFILE_FLAG` is a module-level dict that maps broker tool names to
  `ToolAccess` attribute names.  Tools not in the mapping are excluded
  (safe-fail).  New broker tools should be registered here when added.
- The compiler extracts the system prompt from the first `SESSION_OPENED`
  event payload.  If the ledger has no `SESSION_OPENED` event (e.g. an empty
  ledger), a safe default persona string is used.
- `MEMORY_READ` result summaries from the ledger are surfaced as evidence
  items with source `"ledger:memory_read"`.  They are prepended before
  caller-supplied memory evidence and explicit tool evidence so that prior
  retrieved context appears first.

---

_Created: 2026-03-21_
_Assignee: @copilot_
_Parent Story: US-LAH-002_
