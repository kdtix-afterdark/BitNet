# Task: TASK-LAH-013 Trace Taxonomy and Span Emission

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `tracing`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-014](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-014_eval_hooks_and_audit_artifact_capture.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-007](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-007_tracing_evals_and_audit_spans.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define the canonical trace taxonomy and the span emission points for model, tool, memory, workflow, and approval events.

---

## Context

- **Parent Story AC**: Trace taxonomy and audit continuity
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-014](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-014_eval_hooks_and_audit_artifact_capture.md)

---

## I Know I Am Done When

- [ ] Required span types are documented.
- [ ] Correlation identifiers are documented.
- [ ] Emission points cover the major harness boundaries.

---

## Implementation Notes

### Approach

Use the source plan and the current trace tooling to define a durable taxonomy that later eval and audit work can build on.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Turn trace recorder | `broker/turn_trace.py` | Current trace output |
| Script | Debug monitor | `monitor_broker_debug.py` | Trace consumption |

### Commands / Scripts

```text
tail -f broker_traces/turn-trace.jsonl
```

---

## Constraints

- Do not emit spans that cannot be correlated back to a run or session
- Keep the taxonomy broad enough for future evals but bounded enough to stay readable

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review span taxonomy against plan section 10 | Core boundaries are covered |
| 2 | Review against current trace stream | Taxonomy maps to real events |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-007_
