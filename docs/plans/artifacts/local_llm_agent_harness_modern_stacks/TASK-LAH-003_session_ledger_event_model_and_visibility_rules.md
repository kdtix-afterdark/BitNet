# Task: TASK-LAH-003 Session Ledger Event Model and Visibility Rules

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `ledger`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-002_session_ledger_and_context_compiler.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Map the append-only session ledger event model and visibility rules that the compiler will consume.

---

## Context

- **Parent Story AC**: Ledger source of truth and restart-safe continuity
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md)

---

## I Know I Am Done When

- [ ] Event classes are listed for policy, user, assistant, tool, memory, and artifact activity.
- [ ] Visibility rules are attached to each event class.
- [ ] Ledger events support restart-safe reconstruction.

---

## Implementation Notes

### Approach

Document the event taxonomy and the visibility rules needed for safe model compilation and operational auditing.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Durable state | `broker/durable_state.py` | Existing event behavior |
| Module | Session store | `broker/session_store.py` | Current session representation |

### Commands / Scripts

```text
rg -n "record_|session_open|turn_completed|memory_sync" broker/durable_state.py -S
```

---

## Constraints

- Do not conflate ledger fidelity with model-facing replay fidelity
- Keep ops-only data out of model-visible rules by default

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Compare event list to current durable-state events | Gaps are visible |
| 2 | Review visibility rules against plan guidance | Model/user/ops scopes are clear |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-002_
