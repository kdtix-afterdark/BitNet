# Task: TASK-LAH-008 MCP Lowering and Broker Registration

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `mcp`, `tools`
> **Blocked By**: [TASK-LAH-007](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-007_tool_descriptor_and_policy_contract.md)
> **Blocks**: None

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-004_tool_broker_and_mcp_translation.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define how MCP tools, resources, and prompts are lowered and registered through the unified broker surface.

---

## Context

- **Parent Story AC**: MCP lowering and unified broker behavior
- **Preceding Task**: [TASK-LAH-007](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-007_tool_descriptor_and_policy_contract.md)
- **Blocking Tasks**: None

---

## I Know I Am Done When

- [ ] Lowering rules are documented for tool-only clients.
- [ ] Broker registration behavior is described for native, local, and MCP sources.
- [ ] Approval and trust considerations are called out for remote MCP sources.

---

## Implementation Notes

### Approach

Document how MCP surfaces are normalized into broker registrations and how unsupported surfaces are lowered for clients that only understand tools.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | MCP registry | `broker/mcp.py` | Discovery and server metadata |
| Module | Tool registry | `broker/tools.py` | Broker-facing registration |

### Commands / Scripts

```text
rg -n "mcp|server|tool_manifest|tool_result" broker -S
```

---

## Constraints

- Do not assume all clients support MCP prompts/resources directly
- Keep lowering behavior explicit enough for future adapter work

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review lowering rules against MCP surfaces in the plan | Coverage is complete |
| 2 | Review broker registration model against tool descriptor contract | Registration remains consistent |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-004_
