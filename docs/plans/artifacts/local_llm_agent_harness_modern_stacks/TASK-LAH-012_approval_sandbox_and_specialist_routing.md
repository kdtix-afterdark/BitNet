# Task: TASK-LAH-012 Approval Sandbox and Specialist Routing

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `policy`, `sandbox`
> **Blocked By**: [TASK-LAH-011](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-011_workflow_engine_separation_and_job_semantics.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-006](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-006_workflow_orchestration_and_approvals.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define approval rules, sandbox defaults, and bounded specialist routing for the harness workflow.

---

## Context

- **Parent Story AC**: Specialist routing and approval enforcement
- **Preceding Task**: [TASK-LAH-011](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-011_workflow_engine_separation_and_job_semantics.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] Approval defaults are documented for read-only and mutating actions.
- [ ] Sandbox defaults are documented.
- [ ] Specialist routing is described as a bounded handoff/tool pattern.

---

## Implementation Notes

### Approach

Translate the plan’s policy model into an execution boundary that governs tool use, network access, writes, and specialist delegation.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Tool broker metadata | `broker/tools.py` | Side effects and approval fields |
| Runtime | Broker config | `broker/config.py` | Sandbox defaults |

### Commands / Scripts

```text
rg -n "approval|sandbox|network|read_only|side_effects" broker -S
```

---

## Constraints

- Do not push approval enforcement into prompt text alone
- Keep specialist permissions narrower than the manager’s defaults

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review policy rules against tool descriptor fields | Required controls line up |
| 2 | Review specialist routing against workflow semantics | Boundaries remain explicit |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-006_
