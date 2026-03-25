# User Story: US-LAH-002 Implement append-only session ledger and context compiler

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `ledger`, `context-compiler`
> **Blocks**: US-LAH-005, US-LAH-007
> **Blocked By**: US-LAH-001

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-001_runtime_core_context_compiler.md)  
> **Size**: L (8 pts / 24-40 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want the harness to store runtime state as a ledger and compile model context from structured state,
So that restart behavior, policy visibility, and prompt quality are governed intentionally.
```

---

### TL;DR

Turn session state into an append-only ledger and generate model input from that ledger instead of from a naive transcript replay.

---

### Why This Matters

The plan’s strongest recommendation is to make the session ledger the source of truth and the context compiler the model boundary. Without that split, audit state, approvals, ops metadata, and low-value assistant repetition all bleed into model calls.

---

### Assumptions

- **Roles**: Platform engineer, runtime maintainer
- **Starting point**: Existing broker state, trace, and session code
- **Preconditions**: Canonical contracts are defined

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-001_canonical_runtime_contracts_and_run_profiles.md) | Contract foundation | Blocked |

---

### I Know I Am Done When

- [ ] Ledger events capture policy, user, assistant, tool, memory, and artifact activity clearly.
- [ ] Model-facing context can be compiled from structured state and visibility rules.
- [ ] The compiler excludes non-model operational metadata unless explicitly needed.
- [ ] Later stories can reuse the compiler instead of building prompt logic ad hoc.

---

### Acceptance Criteria

**Scenario 1**: Ledger source of truth
- **Given**: a harness session with multiple event types
- **When**: state is reviewed
- **Then**: the ledger captures the session history as structured events rather than only a transcript

**Scenario 2**: Context compilation
- **Given**: a model turn needs to run
- **When**: the compiler builds model input
- **Then**: only the intended model-visible context is included

**Scenario 3**: Restart-safe continuity
- **Given**: a session resumes after interruption
- **When**: context is rebuilt
- **Then**: the compiler can reconstruct the right working set from ledger and summaries

---

### Constraints

- Do not use the raw prompt as the durable system boundary
- Do not leak auth or ops-only metadata into model input by default

---

### Questions for Engineering

- What visibility flags should exist on every event?
- What compaction and summary boundaries belong in the compiler layer versus the ledger layer?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Extend current durable state incrementally | 8 pts / 24-40 hrs | Faster path. Risk of carrying transcript assumptions forward. |
| B | Rebuild ledger and compiler as new modules | 8 pts / 24-40 hrs | Cleaner separation. Higher migration cost. |
| C | Wrap current state with compiler-first interfaces, then refactor inward | 8 pts / 24-40 hrs | Good migration path. Needs discipline around seams. |

**Recommended**: C because it supports incremental delivery while still creating the right long-term boundary.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| ⚙️ Backend | Y | [TASK-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-003_session_ledger_event_model_and_visibility_rules.md) | 4 |
| ⚙️ Backend | Y | [TASK-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md) | 4 |
| ⚙️ Backend | Y | [TASK-LAH-019](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-019_port_plain_chat_prompting.md) | 3 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Durable state | `broker/durable_state.py` | Ledger source |
| Module | Prompt compiler | `broker/prompting.py` | Model-facing assembly |
| Module | Broker entry | `broker/server.py` | Compiler usage |

---

### Regression Risk

- [ ] Session recovery behavior
- [ ] Prompt assembly and summary shaping

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
