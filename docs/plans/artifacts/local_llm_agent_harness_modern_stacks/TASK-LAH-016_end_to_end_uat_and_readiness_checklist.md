# Task: TASK-LAH-016 End to End UAT and Readiness Checklist

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `uat`, `readiness`
> **Blocked By**: [TASK-LAH-015](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-015_modern_stack_docs_and_run_profiles.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: Medium
> **Parent Story**: [US-LAH-008](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-008_modern_stack_readiness_and_uat.md)
> **Area**: 🧪 Test/Verify
> **Estimate**: 4 hrs

---

## Summary

Define the end-to-end UAT matrix and readiness checklist needed to validate the harness across modern stacks.

---

## Context

- **Parent Story AC**: UAT scenario completeness and rollout evidence
- **Preceding Task**: [TASK-LAH-015](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-015_modern_stack_docs_and_run_profiles.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] UAT scenarios cover backend flexibility, tools/MCP, memory continuity, workflow, approvals, and VS Code Chat validation.
- [ ] The readiness checklist identifies required evidence before rollout.
- [ ] The checklist can be mapped back to Initiative and Epic acceptance.
- [ ] The checklist explicitly separates local Metal-backed BitNet UAT from GitHub-hosted or cloud CPU-only verification.

---

## Implementation Notes

### Approach

Use the run profiles from TASK-LAH-015, the observability design from US-LAH-007, and the VS Code integration story from US-LAH-009 to define the minimum realistic UAT matrix and rollout checklist.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Script | UAT runner | `run_conversation_uat.py` | Scenario execution |
| Script | Debug monitor | `monitor_broker_debug.py` | Live validation support |

### Commands / Scripts

```text
python3 run_conversation_uat.py --help
python3 monitor_broker_debug.py --help
```

---

## Constraints

- Do not rely on narrow smoke tests alone
- Keep the checklist tied to observable evidence and explicit pass/fail outcomes
- Do not blur the line between local Apple Silicon plus Metal validation and CPU-only cloud checks

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review UAT matrix against the initiative scope | Coverage is complete enough for readiness |
| 2 | Review checklist against trace/eval outputs | Required evidence is explicit |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-008_
