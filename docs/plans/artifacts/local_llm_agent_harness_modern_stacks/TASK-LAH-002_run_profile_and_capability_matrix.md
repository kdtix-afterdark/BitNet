# Task: TASK-LAH-002 Run Profile and Capability Matrix

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `runtime`
> **Blocked By**: [TASK-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-001_event_turnresult_and_visibility_contracts.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-001_canonical_runtime_contracts_and_run_profiles.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define the run profile matrix that maps task intent to model family, tool access, sandbox policy, and budget.

---

## Context

- **Parent Story AC**: Shared adapter contract and planning continuity
- **Preceding Task**: [TASK-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-001_event_turnresult_and_visibility_contracts.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] Run profile fields are documented.
- [ ] Capability dimensions are mapped per profile.
- [ ] The matrix is usable by adapter and workflow stories.

---

## Implementation Notes

### Approach

Convert `requestType`-style intent into a stable run profile model that expresses model, tool, memory, and sandbox behavior without embedding provider detail.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Plan | Harness architecture | `docs/plans/local_llm_agent_harness_modern_stacks.md` | Context compiler guidance |
| Runtime | Broker config | `broker/config.py` | Current runtime knobs |

### Commands / Scripts

```text
rg -n "requestType|profile|sandbox|tool" broker -S
```

---

## Constraints

- Do not hardcode one provider’s feature names into the canonical matrix
- Keep profile behavior understandable enough for project planning

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review run profile matrix against planned adapters | Each adapter can consume it |
| 2 | Review with policy and tool stories | Required fields are present |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-001_
