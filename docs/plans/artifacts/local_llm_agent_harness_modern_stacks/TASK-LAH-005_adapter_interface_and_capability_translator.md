# Task: TASK-LAH-005 Adapter Interface and Capability Translator

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `adapters`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-006](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-006_responses_anthropic_and_local_adapter_implementation.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-003_provider_adapter_layer.md)
> **Area**: 🔍 Research/Spike
> **Estimate**: 3 hrs

---

## Summary

Define the provider adapter interface and the capability-translation rules shared by all backend adapters.

The sequence this task should support is:

1. Responses-compatible adapter
2. MCP-driven broker integration in the next story
3. Anthropic Messages adapter
4. Native local fallback only if a required backend cannot stay behind a Responses-compatible surface

---

## Context

- **Parent Story AC**: Shared adapter contract and provider separation
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-006](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-006_responses_anthropic_and_local_adapter_implementation.md)

---

## I Know I Am Done When

- [ ] Adapter interface inputs and outputs are documented.
- [ ] Capability translation rules are listed.
- [ ] Provider-specific artifacts are clearly scoped to the adapter boundary.

---

## Implementation Notes

### Approach

Translate the plan’s provider-adapter guidance into one reusable interface definition and a capability matrix for supported backend families, while making the Responses-compatible path the first concrete implementation target.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Plan | Adapter guidance | `docs/plans/local_llm_agent_harness_modern_stacks.md` | Primary source |
| Module | Local runtime | `broker/llama_runtime.py` | Existing local backend |

### Commands / Scripts

```text
rg -n "runtime|chat_payload|responses|anthropic" broker -S
```

---

## Constraints

- Do not mix orchestration logic into the adapter interface
- Keep the capability matrix readable enough for planning and review
- Do not force a dedicated native fallback adapter unless a real compatibility gap is identified

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review interface against run profiles | Required adapter inputs are present |
| 2 | Review against planned backend families | Translation rules cover each target |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-003_
