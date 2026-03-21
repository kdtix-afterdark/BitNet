# TASK-LAH-002 — Run Profile and Capability Matrix

_Imported from issue [TASK-LAH-002](https://github.com/kdtix-afterdark/BitNet/issues/17) on 2026-03-21._

## Summary

Define the run profile matrix that maps task intent to model family, tool
access, sandbox policy, and budget.

---

## Status

**Complete.**

---

## Implementation

### New module: `broker/run_profile.py`

The run profile model is implemented as four composable dataclasses plus a
top-level `RunProfile` descriptor.

#### Sub-policy dataclasses

| Class | Fields | Purpose |
|---|---|---|
| `SandboxPolicy` | `allow_read`, `allow_write`, `allow_network`, `allow_exec` | Execution permissions |
| `ToolAccess` | `filesystem_read`, `filesystem_write`, `mcp_memory`, `mcp_sequential_thinking`, `mcp_context7`, `mcp_custom`, `allow_tool_names`, `deny_tool_names` | Tool-category permissions |
| `MemoryPolicy` | `enabled`, `routing_priority`, `auto_store` | Memory-routing behaviour |
| `ModelBudget` | `ctx_size`, `max_new_tokens`, `temperature` | Token and temperature budget |

#### RunProfile

```
name            str   – unique key in RUN_PROFILE_MATRIX
description     str   – human-readable use-case summary
model_family    str   – "fast" | "balanced" | "high-capacity"
tool_access     ToolAccess
memory_policy   MemoryPolicy
sandbox_policy  SandboxPolicy
budget          ModelBudget
```

#### Canonical profile matrix

| Profile | model_family | fs read | fs write | mcp memory | seq-thinking | ctx7 | mcp custom | memory routing | allow write | allow network | ctx | max tokens | temp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `default` | balanced | ✓ | — | — | — | — | — | model_first | — | — | 2 048 | 512 | 0.2 |
| `read_only` | fast | ✓ | — | — | — | — | — | model_first | — | — | 2 048 | 256 | 0.1 |
| `memory_first` | balanced | ✓ | — | ✓ | — | — | — | memory_first | ✓ | — | 4 096 | 512 | 0.2 |
| `tool_heavy` | high-capacity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | memory_first | ✓ | ✓ | 8 192 | 1 024 | 0.3 |
| `thinking` | high-capacity | ✓ | — | — | ✓ | — | — | model_first | — | — | 8 192 | 2 048 | 0.4 |

#### Helper functions / constants

| Symbol | Type | Description |
|---|---|---|
| `RUN_PROFILE_MATRIX` | `Dict[str, RunProfile]` | Canonical registry; key is profile name |
| `resolve_profile(name)` | function | Returns named profile, falling back to `"default"` |
| `PROFILE_NAMES` | `List[str]` | Ordered list of canonical profile names |

### Updated doc: `docs/plans/local_llm_agent_harness_modern_stacks.md`

§11 added — *Run Profile and Capability Matrix* — documents the sub-policy
dataclasses, RunProfile fields, the full capability matrix, and a usage
example.

---

## Verification

| Step | Action | Result |
|---|---|---|
| 1 | Review `RUN_PROFILE_MATRIX` against planned adapters | Each adapter can consume it via `resolve_profile()` |
| 2 | Review with policy and tool stories | All required fields (`tool_access`, `sandbox_policy`, `memory_policy`, `budget`) are present |
| 3 | `resolve_profile("unknown")` returns `"default"` profile | Safe fallback confirmed |

---

## Constraints Met

- No provider-specific feature names appear in the canonical matrix; model
  selection uses the coarse `model_family` tier only.
- Sub-policy dataclasses are independently composable.
- `resolve_profile()` provides a safe fallback so downstream callers are
  never blocked by an unrecognised name.

---

_Created: 2026-03-21_
_Assignee: @copilot_
_Parent Story: US-LAH-001_
