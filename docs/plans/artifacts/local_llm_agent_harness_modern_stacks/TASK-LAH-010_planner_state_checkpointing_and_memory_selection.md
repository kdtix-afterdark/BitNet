# Task: TASK-LAH-010 Planner State Checkpointing and Memory Selection

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `memory`, `planner`
> **Blocked By**: [TASK-LAH-009](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-009_memory_layer_contract_and_retention_rules.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-005](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-005_memory_layers_and_planner_state.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define the explicit planner state object and how checkpoints select and preserve the right memory.

---

## Context

- **Parent Story AC**: Explicit planning and layered continuity
- **Preceding Task**: [TASK-LAH-009](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-009_memory_layer_contract_and_retention_rules.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] Planner state fields are defined.
- [ ] Checkpoint rules are defined.
- [ ] Memory selection logic is aligned with planner and workflow needs.

---

## Implementation Notes

### Approach

Use the source plan’s explicit planner shape to define checkpointable planning state and the memory inputs that should feed it.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Plan | Planner example | `docs/plans/local_llm_agent_harness_modern_stacks.md` | Explicit planning model |
| Module | Durable state | `broker/durable_state.py` | Checkpoint behavior |

### Commands / Scripts

```text
rg -n "summary|checkpoint|pending_sync|turn_count" broker/durable_state.py -S
```

---

## Constraints

- Do not store provider-hidden reasoning as planner state
- Keep planner state auditable and resumable

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review planner state against memory-layer rules | Inputs and outputs align |
| 2 | Review checkpoint rules against workflow needs | Resume behavior is supported |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-005_
