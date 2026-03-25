# Task: TASK-LAH-007 Tool Descriptor and Policy Contract

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `tools`, `policy`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-008](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-008_mcp_lowering_and_broker_registration.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-004_tool_broker_and_mcp_translation.md)
> **Area**: ⚙️ Backend
> **Estimate**: 4 hrs

---

## Summary

Define the canonical `ToolDescriptor` and the policy metadata that every tool path must expose.

---

## Context

- **Parent Story AC**: Unified tool metadata and policy readiness
- **Preceding Task**: None
- **Blocking Tasks**: [TASK-LAH-008](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-008_mcp_lowering_and_broker_registration.md)

---

## I Know I Am Done When

- [ ] Required tool descriptor fields are documented.
- [ ] Policy fields cover side effects, auth scope, timeout, and approvals.
- [ ] The descriptor works for native, local, and MCP tools.

---

## Implementation Notes

### Approach

Translate the plan’s tool broker shape into a practical descriptor contract the runtime, policy layer, and MCP lowering path can all share.

### Code Areas

| Type | Object | Location | Notes |
| --- | --- | --- | --- |
| Module | Tool registry | `broker/tools.py` | Current tool catalog |
| Module | MCP registry | `broker/mcp.py` | Source metadata for MCP tools |

### Commands / Scripts

```text
rg -n "tool|mcp|schema|approval" broker -S
```

---

## Constraints

- Do not define separate metadata models for local versus MCP tools
- Keep policy fields concrete enough for workflow enforcement

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Review descriptor against native/local/MCP examples | All tool classes fit |
| 2 | Review policy fields against approval story needs | Required governance fields exist |

---

## Notes / Findings

- 

---

_Created: 2026-03-21_
_Assignee: TBD_
_Parent Story: US-LAH-004_
