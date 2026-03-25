# Task: TASK-LAH-018 VS Code Model Provider Extension and UAT Path

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `vscode`, `lm-provider`, `uat`
> **Blocked By**: [TASK-LAH-017](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-017_responses_endpoint_and_vscode_integration_contract.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-009](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-009_vscode_chat_integration_via_responses_provider.md)
> **Area**: 🖥️ UI
> **Estimate**: 4 hrs

---

## Summary

Define the productized VS Code model-provider extension path and the repeatable UAT flow that will validate BitNet inside VS Code Chat.

---

## Context

- **Parent Story AC**: VS Code model-provider integration, trace-backed UAT, long-term supportability
- **Preceding Task**: [TASK-LAH-017](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-017_responses_endpoint_and_vscode_integration_contract.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] The extension structure, settings, and activation expectations are defined.
- [ ] Reachability and error handling expectations are documented for broker-up and broker-down cases.
- [ ] The VS Code UAT flow can be mapped to broker session state and trace evidence.

---

## Implementation Notes

### Approach

Describe the owned VS Code model-provider integration path and the minimum UAT flow needed to keep it supportable as a long-term product surface.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Folder | VS Code extension | `vscode-bitnet-provider/` | Planned integration package |
| Script | UAT runner | `run_conversation_uat.py` | Scenario coordination |
| Script | Debug monitor | `monitor_broker_debug.py` | Evidence correlation |

### Commands / Scripts

```text
python3 monitor_broker_debug.py --help
python3 run_conversation_uat.py --help
```

---

## Constraints

- Do not rely on modifying GitHub-controlled model selection backends
- Keep setup, settings, and error handling explicit enough for long-term ownership

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review extension flow against the broker contract | Integration boundary is coherent |
| 2 | Review VS Code UAT flow against trace/state capture | Evidence path is complete |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-009_
