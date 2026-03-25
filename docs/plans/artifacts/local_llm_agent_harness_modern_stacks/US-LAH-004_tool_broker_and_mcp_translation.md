# User Story: US-LAH-004 Normalize tool broker and MCP translation for Copilot-first workflows

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `tools`, `mcp`
> **Blocks**: US-LAH-006, US-LAH-007, US-LAH-008
> **Blocked By**: US-LAH-003

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-002_provider_adapters_and_tool_broker.md)  
> **Size**: L (8 pts / 24-40 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want one broker surface for native tools, local functions, and MCP tools,
So that the harness can apply the same governance and discovery model across all tool sources.
```

---

### TL;DR

Create one tool broker contract that can normalize local, native, and MCP tool behavior, with MCP tools prioritized for GitHub Copilot Chat and Warp workflows.

---

### Why This Matters

The plan calls out a canonical tool descriptor and emphasizes that MCP tools, resources, and prompts should be normalized through a broker layer. This is especially important here because the highest-frequency daily surfaces are GitHub Copilot Chat and Warp, both of which benefit directly from a strong MCP-first broker seam.

---

### Assumptions

- **Roles**: Platform engineer, tooling maintainer
- **Starting point**: Adapter layer is defined
- **Preconditions**: Canonical tool metadata is available from prior contract work

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-003_provider_adapter_layer.md) | Adapter foundation | Blocked |

---

### I Know I Am Done When

- [ ] The harness has one `ToolDescriptor` model with policy-relevant metadata.
- [ ] Native, local, and MCP tools can be represented consistently through the broker.
- [ ] MCP lowering rules are clear for clients that only support tool surfaces.
- [ ] The broker path needed for Copilot-first workflows is defined before broader adapter expansion continues.
- [ ] Downstream workflow and policy stories can consume one tool broker contract.

---

### Acceptance Criteria

**Scenario 1**: Unified tool metadata
- **Given**: a native tool, local function, and MCP tool
- **When**: they are reviewed through the broker design
- **Then**: they share one descriptor model for runtime use

**Scenario 2**: MCP lowering
- **Given**: a client that supports only tools
- **When**: MCP resources or prompts need to be used
- **Then**: the broker can define how to lower them into supported context

**Scenario 3**: Policy readiness
- **Given**: future approval and sandbox rules
- **When**: tool execution paths are planned
- **Then**: policy fields already exist on the tool descriptors

**Scenario 4**: Copilot-first enablement
- **Given**: the team’s primary daily use of GitHub Copilot Chat and Warp
- **When**: the epic is sequenced for delivery
- **Then**: MCP broker work lands before Anthropic-specific adapter expansion

---

### Constraints

- Do not couple tool metadata to a single provider API
- Do not assume all MCP clients support resources and prompts directly

---

### Questions for Engineering

- Which MCP surfaces must be lowered in milestone one?
- What minimum policy metadata is required on every tool descriptor?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Extend current tool registry directly | 8 pts / 24-40 hrs | Fast path. May preserve old assumptions. |
| B | Introduce a broker abstraction first, then migrate tools | 8 pts / 24-40 hrs | Cleaner long-term seam. More up-front design. |
| C | Parallel broker and registry models | 8 pts / 24-40 hrs | Easier comparison. Risk of duplicated effort. |

**Recommended**: B because policy, MCP lowering, and workflow all need one durable broker boundary, and it aligns with the team’s highest-value daily integration path.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| ⚙️ Backend | Y | [TASK-LAH-007](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-007_tool_descriptor_and_policy_contract.md) | 4 |
| ⚙️ Backend | Y | [TASK-LAH-008](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-008_mcp_lowering_and_broker_registration.md) | 4 |
| 🧪 Test/Verify | Y | Validate descriptor coverage for native, local, and MCP tools | 3 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Tool registry | `broker/tools.py` | Existing registration surface |
| Module | MCP registry | `broker/mcp.py` | MCP source discovery |

---

### Regression Risk

- [ ] Tool discovery and invocation behavior
- [ ] MCP compatibility across clients

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
