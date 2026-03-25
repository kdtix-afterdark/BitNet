# Task: TASK-LAH-006 Responses-First Adapter Implementation and Follow-On Sequencing

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `adapters`
> **Blocked By**: [TASK-LAH-005](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-005_adapter_interface_and_capability_translator.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-003_provider_adapter_layer.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Map the first implementation slice for a Responses-compatible adapter, then define the checkpoints for later Anthropic and native fallback work.

---

## Context

- **Parent Story AC**: Provider separation and local backend support
- **Preceding Task**: [TASK-LAH-005](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-005_adapter_interface_and_capability_translator.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] Responses-compatible adapter responsibilities are defined as the first implementation slice.
- [ ] Follow-on Anthropic work is explicitly sequenced after MCP broker delivery.
- [ ] Native fallback work is gated behind a proven compatibility need.
- [ ] Shared translator logic versus backend-specific logic is documented.
- [ ] Verification expectations exist for each backend family.

---

## Implementation Notes

### Approach

Use the interface from TASK-LAH-005 to describe the first concrete Responses-compatible adapter module, then define the follow-on checkpoints for Anthropic and native fallback targets.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Local runtime | `broker/llama_runtime.py` | Local-compatible path |
| Module | Future adapters | `broker/` | New adapter layer |

### Commands / Scripts

```text
python3 run_broker.py --help
```

---

## Constraints

- Do not treat unsupported provider features as mandatory for milestone one
- Keep verification paths explicit for each backend family
- Do not implement native local fallback ahead of MCP broker delivery unless the local hosting surface cannot stay Responses-compatible

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review adapter slice per backend family | Responsibilities are clear |
| 2 | Review verification path per adapter | Test expectations are concrete |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-003_
