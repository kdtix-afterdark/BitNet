# Task: TASK-LAH-011 Workflow Engine Separation and Job Semantics

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `workflow`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-012](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-012_approval_sandbox_and_specialist_routing.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-006](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-006_workflow_orchestration_and_approvals.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define the durable workflow loop and its job semantics separately from the per-turn execution loop.

---

## Context

- **Parent Story AC**: Workflow separation
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-012](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-012_approval_sandbox_and_specialist_routing.md)

---

## I Know I Am Done When

- [ ] Turn loop and workflow loop responsibilities are separated.
- [ ] Retry, timeout, and resume semantics are documented.
- [ ] Job identity and checkpoint relationships are clear.

---

## Implementation Notes

### Approach

Describe the workflow layer as the durable job runner around the turn engine, including status, retries, resumptions, and checkpoint interaction.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Broker runtime | `broker/server.py` | Current turn execution |
| Module | Durable state | `broker/durable_state.py` | Resume/checkpoint seams |

### Commands / Scripts

```text
rg -n "retry|timeout|shutdown|heartbeat|pending_sync" broker -S
```

---

## Constraints

- Do not leave retry and resume behavior implicit in chat handling
- Keep job semantics deterministic enough for operational support

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review workflow semantics against plan section 7 | Separation is clear |
| 2 | Review against current broker restart behavior | Resume hooks are accounted for |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-006_
