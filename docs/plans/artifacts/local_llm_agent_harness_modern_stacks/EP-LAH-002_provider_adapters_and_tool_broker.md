# Epic: EP-LAH-002 Provider Adapters and Tool Broker

> **Issue Type**: Epic
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Repository**: `kdtix-afterdark/BitNet`
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `adapters`, `mcp`, `tools`
> **Parent Initiative**: [INIT-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/INIT-LAH-001_initiative.md)
> **Blocks**: EP-LAH-003, EP-LAH-004, US-LAH-003, US-LAH-004
> **Blocked By**: EP-LAH-001

> Jira Level 3 — sits under an Initiative, groups User Stories.
> Product fills the 📋 PRODUCT SECTION. Tech Lead fills the ⚙️ TECH LEAD SECTION.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Tech Lead section.

---

> **Status**: Draft  
> **Priority**: High  
> **Target Release**: TBD  
> **Epic Owner**: Chris Kreager  
> **Total Points**: 13

---

## 📋 PRODUCT SECTION

### Objective

Make the harness flexible enough to talk to hosted and local model stacks through adapters and one unified broker surface for tools and MCP.

### Release Value

After this epic, teams can plug the same harness into different model backends and tool ecosystems without rewriting the core runtime.

### Delivery Order

This epic should be delivered in the following practical sequence to match the team’s actual IDE and agent usage patterns:

1. Responses-compatible adapter foundation for Codex and local Responses-compatible endpoints
2. MCP tool broker and lowering path for GitHub Copilot Chat and Warp-centric workflows
3. Anthropic Messages adapter to prove provider portability across a meaningfully different transport
4. Native local fallback adapter only if a required local backend cannot stay behind a Responses-compatible surface

### Success Criteria

- [ ] The harness can translate its internal turn model into more than one provider/backend shape.
- [ ] Tools are described once and enforced consistently through one broker boundary.
- [ ] MCP integration can be lowered appropriately for clients that only support tools.

---

### Feature Scope

| # | Feature/Capability | What It Includes | What It Enables |
|---|-------------------|------------------|-----------------|
| 1 | Responses-compatible adapter foundation | Responses-style translation and local Responses-compatible targeting | Best-fit first transport for Codex-driven workflows |
| 2 | Unified tool broker | Canonical tool descriptors and policy metadata, prioritized for Copilot/Warp MCP usage | Consistent tool governance where the team works most |
| 3 | MCP lowering | Mapping tools/resources/prompts into supported client surfaces | Broad MCP compatibility |
| 4 | Follow-on adapters | Anthropic Messages translation and native fallback only if still required | Backend portability without premature adapter sprawl |

---

### Assumptions

- Core contracts from EP-LAH-001 are available before implementation starts.
- The first milestone can target a narrow but representative set of adapters.

---

### Dependencies

| Dependency | Type | Owner | Status |
|------------|------|-------|--------|
| EP-LAH-001 | Blocker | Chris Kreager | Draft |

---

### Out of Scope

- Full support for every provider-native feature
- Unbounded third-party MCP trust and policy models

---

### Artifacts

- [ ] Figma / Jira Comps: N/A
- [x] Workflow Diagram: [local_llm_agent_harness_modern_stacks.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/local_llm_agent_harness_modern_stacks.md)
- [ ] [Other artifacts]

---

### I Know I Am Done When

- [ ] Adapter responsibilities are separated cleanly from runtime core concerns.
- [ ] Tool broker behavior is defined well enough to support native, local, and MCP tools.
- [ ] Story outputs can be validated with representative provider and tool flows.

---

### User Stories

| Order | # | Story Title | Description | Points | Hours | Dependencies | QA Can Test |
|-------|---|-------------|-------------|--------|-------|--------------|-------------|
| 1 | US-LAH-003 | Implement provider adapter layer with Responses-compatible first delivery | Create the capability translation boundary around the canonical turn model, with Responses-compatible transport as the first concrete target. | 5 | 20 | EP-LAH-001 | Yes |
| 2 | US-LAH-004 | Normalize tool broker and MCP translation for Copilot-first workflows | Define and implement the unified tool broker and MCP lowering strategy used most heavily by GitHub Copilot Chat and Warp workflows. | 8 | 36 | US-LAH-003 | Yes |
| | | | **Total** | **13** | **56** | | |

**Sequence & Sizing Rationale:**
- Development efficiency: the Responses-compatible transport lands first because it is the best fit for Codex and local Responses-compatible endpoints.
- Risk reduction: MCP/tool-broker work lands second because that is the highest-leverage integration path for day-to-day Copilot Chat and Warp usage.
- Value delivery: Anthropic is deferred until after the broker seam exists, and native local fallback is intentionally last so we do not build an extra adapter if a Responses-compatible local surface is sufficient.

---

### Questions for Tech Lead

- Which adapter behaviors must be normalized and which can remain provider-specific?
- What minimum MCP lowering rules are needed for the first release?

---

## ⚙️ TECH LEAD SECTION

### Impacted Functional Areas

| Functional Area | Impact Level | Primary Files | Notes |
|-----------------|--------------|---------------|-------|
| LLM runtime | High | `broker/llama_runtime.py` and future adapter modules | Translation boundary |
| Tooling | High | `broker/tools.py`, `broker/mcp.py` | Descriptor normalization |
| Policy | Medium | Tool approval and allowlist behavior | Provider-aware controls |

---

### High-Level Technical Notes

- Provider adapters should translate capabilities, not rewrite business logic.
- MCP support should normalize tools first and lower resources/prompts when a client lacks native support.
- The first concrete adapter target should be Responses-compatible transport; Anthropic should validate portability after the MCP broker seam is working.
- Native local fallback should be gated by need, not built automatically if local model hosting can sit behind a Responses-compatible endpoint.

---

### Code Areas to Examine

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Runtime transport | `broker/llama_runtime.py` | Local backend target |
| Module | Tool registry | `broker/tools.py` | Canonical tool catalog |
| Module | MCP registry | `broker/mcp.py` | MCP discovery and access |

---

### Database Considerations

| Change Type | Object | Migration Script Needed |
|-------------|--------|------------------------|
| N/A | N/A | No |

---

### Shared Components

- Canonical tool descriptor: Used in Stories US-LAH-003 and US-LAH-004

---

### Technical Dependencies

| System/API | What's Needed | Status |
|------------|---------------|--------|
| OpenAI-compatible local endpoint | Adapter target | Available |
| MCP servers | Tool and prompt/resource surfaces | Available |

---

### Cross-Area Impacts

| Area | Why It May Be Impacted | Mitigation |
|------|----------------------|------------|
| Memory/workflow | Adapter/tool output shapes influence downstream workflow inputs | Keep TurnResult contract stable |

---

### Potential Conflicts

- Provider changes may force updates to adapter capability matrices.

---

### Performance Considerations

- Tool broker translation should not add unnecessary latency or payload bloat.

---

### Security/Compliance

- Remote MCP and native provider tools must respect approval and allowlist policy.

---

### Regression Risk Areas

- [ ] Tool invocation behavior
- [ ] MCP server interoperability
- [ ] Provider-specific request assembly

---

### Spike Needed?

- [x] Yes - adapter and MCP capability mapping needs validation before implementation
- [ ] No

---

_Last Updated: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Technical Analysis By: Codex_
