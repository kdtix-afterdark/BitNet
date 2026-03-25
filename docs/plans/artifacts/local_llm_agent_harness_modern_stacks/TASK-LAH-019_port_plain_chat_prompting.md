# Task: TASK-LAH-019 Port Plain-Chat Prompting

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `context-compiler`, `prompting`, `found in UAT`
> **Blocked By**: [TASK-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md)
> **Blocks**: [TASK-LAH-016](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-016_end_to_end_uat_and_readiness_checklist.md)

> Jira Subtask — sits under a User Story (Level 4). Smallest trackable unit of work.
> Subtasks are engineering-owned. No product section — the parent Story carries the business context.
> **Target duration**: 1–4 hours. If it exceeds 4 hours, split it or re-evaluate the parent Story breakdown.

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-002_session_ledger_and_context_compiler.md)
> **Area**: ⚙️ Backend
> **Estimate**: 3 hrs

---

## Summary

Port the stable plain-chat prompting behavior into the tracked broker path so ordinary no-evidence turns remain plain while evidence-backed turns stay grounded.

---

## Context

- **Parent Story AC**: Context compilation includes only intended model-visible state and avoids ad hoc prompt shaping drift
- **Preceding Task**: [TASK-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md)
- **Blocking Tasks**: [TASK-LAH-016](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-016_end_to_end_uat_and_readiness_checklist.md)

---

## I Know I Am Done When

- [ ] Ordinary no-evidence chat turns compile to plain user text instead of an unconditional `Evidence` / `Task` wrapper.
- [ ] Evidence-backed turns still compile to the grounded `Evidence` / `Task` structure.
- [ ] Regression tests cover both no-evidence and evidence-backed paths so the UAT finding cannot reappear silently.

---

## Implementation Notes

### Approach

Carry the stable lab behavior into the tracked broker code path by making prompt grounding conditional on real evidence, then lock that behavior down with regression coverage and trace-based verification.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Prompt builder | `broker/prompting.py` | Add or preserve conditional grounding for plain chat |
| Module | Broker entry | `broker/server.py` | Pass grounded-user intent only when evidence exists |
| Test | Prompting regressions | `tests/test_prompting.py` | Cover plain-chat and evidence-backed turns |
| Trace | Turn traces | `broker_traces/turn-trace.jsonl` | Verify compiled payload shape during UAT rerun |

### Commands / Scripts

```text
python3 -m unittest discover -s tests -v
python3 run_conversation_uat.py --conversation conversations/conversation.test02.json --broker-url http://127.0.0.1:8091 --reset
```

---

## Constraints

- Do not weaken evidence-backed prompt grounding to avoid the crash; preserve the intended grounded path when evidence exists
- Do not treat output trimming as a substitute for fixing the compiler boundary

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Run prompt regression coverage after the port | Plain chat and grounded chat both behave as intended |
| 2 | Re-run UAT with turn tracing enabled | The compiled no-evidence user turn is plain text and the session no longer depends on local-only prompt behavior |

---

## Notes / Findings

- Found during Apple Silicon Metal UAT alignment while comparing PR 37 against the stable `/tmp` lab state
- This task exists to prevent the UAT report from depending on a local-only prompt compiler behavior

---

_Created: 2026-03-24_
_Assignee: TBD_
_Parent Story: US-LAH-002_
