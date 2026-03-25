# Task: TASK-LAH-004 Context Compiler Assembly and Regression Coverage

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `context-compiler`
> **Blocked By**: [TASK-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-003_session_ledger_event_model_and_visibility_rules.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-002_session_ledger_and_context_compiler.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define the context compiler assembly flow and the regression checks needed to keep model-facing payloads intentional.

---

## Context

- **Parent Story AC**: Context compilation and restart-safe continuity
- **Preceding Task**: [TASK-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-003_session_ledger_event_model_and_visibility_rules.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] Compiler inputs and outputs are documented.
- [ ] Model-facing inclusion rules are documented.
- [ ] Regression coverage expectations are listed.

---

## Implementation Notes

### Approach

Describe how the compiler consumes ledger state, summaries, run profile, tools, and selected memory, then define the regression scenarios that protect those rules.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Prompting | `broker/prompting.py` | Current assembly path |
| Module | Broker server | `broker/server.py` | Compiler invocation |

### Commands / Scripts

```text
python3 -m unittest tests.test_prompting -v
```

---

## Constraints

- Do not reintroduce transcript-only replay as the compiler boundary
- Keep regression checks focused on model-facing behavior, not only storage behavior

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review compiler path against harness plan | Inputs and outputs align |
| 2 | Review expected regression scenarios | Replay and prompt-shaping risks are covered |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-002_
