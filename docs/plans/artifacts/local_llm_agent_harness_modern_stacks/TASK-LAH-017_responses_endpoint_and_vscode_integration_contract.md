# Task: TASK-LAH-017 Responses Endpoint and VS Code Integration Contract

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `responses`, `vscode`, `integration`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-018](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-018_vscode_model_provider_extension_and_uat_path.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-009](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-009_vscode_chat_integration_via_responses_provider.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define the Responses/OpenAI-compatible broker surface and integration contract that the VS Code model-provider path should target.

---

## Context

- **Parent Story AC**: Standardized endpoint and long-term supportability
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-018](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-018_vscode_model_provider_extension_and_uat_path.md)

---

## I Know I Am Done When

- [ ] The minimum Responses/OpenAI-compatible request and response contract is documented.
- [ ] Streaming, model identity, configuration, and correlation expectations are defined.
- [ ] The contract is explicitly positioned as the VS Code integration target instead of the bespoke `/chat` path.

---

## Implementation Notes

### Approach

Define the smallest stable broker surface that can support a productized VS Code model-provider path and keep it aligned with the broader adapter strategy.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Broker API | `broker/server.py` | Endpoint exposure |
| Module | Runtime transport | `broker/llama_runtime.py` | Model-facing translation |
| Plan | Harness plan | `docs/plans/local_llm_agent_harness_modern_stacks.md` | Architectural source |

### Commands / Scripts

```text
python3 run_broker.py --help
rg -n "chat|responses|stream" broker -S
```

---

## Constraints

- Do not lock the contract to the existing `/chat` payload shape
- Keep correlation hooks compatible with trace and UAT evidence capture

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review contract against story acceptance criteria | Required endpoint behaviors are covered |
| 2 | Review contract against broker trace/UAT needs | Correlation requirements are explicit |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-009_
