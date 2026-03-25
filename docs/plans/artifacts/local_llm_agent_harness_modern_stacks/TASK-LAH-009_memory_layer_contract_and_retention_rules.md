# Task: TASK-LAH-009 Memory Layer Contract and Retention Rules

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `memory`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-010](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-010_planner_state_checkpointing_and_memory_selection.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-005](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-005_memory_layers_and_planner_state.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define hot, warm, and cold memory responsibilities plus retention rules for each layer.

---

## Context

- **Parent Story AC**: Layered continuity and provider independence
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-010](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-010_planner_state_checkpointing_and_memory_selection.md)

---

## I Know I Am Done When

- [ ] Each memory layer has a clear purpose.
- [ ] Retention and compaction rules are defined.
- [ ] Durable facts are separated from ephemeral working context.

---

## Implementation Notes

### Approach

Translate the plan’s hot/warm/cold model into explicit retention guidance that later workflow and planner tasks can rely on.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Durable state | `broker/durable_state.py` | Summaries and checkpoints |
| Module | Memory routing | `broker/memory_routing.py` | Retrieval/persistence paths |

### Commands / Scripts

```text
rg -n "summary|checkpoint|memory" broker -S
```

---

## Constraints

- Do not treat the full transcript as the only retained memory
- Keep retention rules explainable enough for UAT and audit use

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review layer definitions against the source plan | Hot/warm/cold intent is preserved |
| 2 | Review retention rules against restart and compaction needs | Rules support continuity |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-005_
