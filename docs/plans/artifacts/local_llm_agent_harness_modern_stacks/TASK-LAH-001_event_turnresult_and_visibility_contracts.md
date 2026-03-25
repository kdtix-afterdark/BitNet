# Task: TASK-LAH-001 Event TurnResult and Visibility Contracts

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `runtime`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-002_run_profile_and_capability_matrix.md)

> Jira Subtask — sits under a User Story (Level 4). Smallest trackable unit of work.
> Subtasks are engineering-owned. No product section — the parent Story carries the business context.
> **Target duration**: 1–4 hours. If it exceeds 4 hours, split it or re-evaluate the parent Story breakdown.

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-001_canonical_runtime_contracts_and_run_profiles.md)
> **Area**: 🔍 Research/Spike
> **Estimate**: 3 hrs

---

## Summary

Define the first draft of canonical `Event`, `TurnResult`, and visibility metadata fields for the harness.

---

## Context

- **Parent Story AC**: Shared contract review and adapter readiness
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-002_run_profile_and_capability_matrix.md)

---

## I Know I Am Done When

- [ ] Required `Event` fields are listed.
- [ ] `TurnResult` fields are listed.
- [ ] Visibility flags are defined for model, user, and ops audiences.

---

## Implementation Notes

### Approach

Extract the contract requirements from the plan and current broker traces, then record a normalized field list that downstream tasks can reference.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Plan | Harness architecture | `docs/plans/local_llm_agent_harness_modern_stacks.md` | Primary source |
| Trace | Turn trace schema | `broker/turn_trace.py` | Current event evidence |

### Commands / Scripts

```text
rg -n "turn|trace|event|result" broker -S
```

---

## Constraints

- Do not include provider-specific transport fields as canonical contract requirements
- Assume the parent Story owns final contract approval

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review field list against plan sections 1, 6, and 10 | Canonical fields are covered |
| 2 | Review against current broker trace artifacts | Existing runtime evidence maps cleanly |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-001_
