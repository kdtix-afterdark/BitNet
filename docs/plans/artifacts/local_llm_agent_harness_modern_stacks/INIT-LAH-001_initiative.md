# Initiative: INIT-LAH-001 Provider-Neutral Local Agent Harness Foundation

> **Issue Type**: Initiative
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Repository**: `kdtix-afterdark/BitNet`
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `local-llm`, `architecture`
> **Parent Project Scope**: [PS-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/PS-LAH-001_project_scope.md)
> **Blocks**: EP-LAH-001, EP-LAH-002, EP-LAH-003, EP-LAH-004
> **Blocked By**: PS-LAH-001

> Jira Level 2 — sits under a Project Scope, groups 1–4 Epics.
> Product fills the 📋 PRODUCT SECTION. Tech Lead fills the ⚙️ TECH LEAD SECTION.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Tech Lead section.

---

> **Status**: Draft
> **Priority**: High
> **Target Release**: TBD
> **Initiative Owner**: Chris Kreager
> **Total Points**: 52

---

## 📋 PRODUCT SECTION

### Objective

Create a durable, provider-neutral local agent harness so teams can build and operate local-first agent workflows without tying core runtime design to one provider’s chat format. Without this, every provider or tooling change risks rework across prompts, tools, memory, approvals, and observability.

---

### Release Value

When this initiative ships, teams can run a single local-first agent harness architecture across modern stacks with clear separation between session state, model-facing context, tools and MCP, workflow control, memory, and operational observability. That reduces integration churn and gives the team a reusable foundation for future agent features.

---

### Success Criteria

- [ ] A canonical runtime model exists for session events, run profiles, tool descriptors, and turn results.
- [ ] The harness can target multiple provider/backend shapes through adapters rather than one transcript-specific implementation.
- [ ] Delivery teams can reason about memory, approvals, tracing, and workflow independently from the raw model transcript.

---

### Feature Scope

| # | Feature/Capability | What It Includes | What It Enables |
|---|-------------------|------------------|------------------|
| 1 | Runtime core | Session ledger, context compiler, run profiles, canonical contracts | Stable model input construction and restart-safe execution |
| 2 | Execution fabric | Responses-compatible adapter first, Copilot-first MCP broker second, then Anthropic and only-when-needed native fallback | Multi-provider and local-backend flexibility |
| 3 | Control planes | Memory layers, workflow engine, policy and approvals | Safe, resumable, governed agent runs |
| 4 | Operational readiness | Tracing, evals, VS Code integration, docs, UAT | Observable rollout and repeatable validation |

---

### Assumptions

- The first delivery can focus on the architectural foundation and issue hierarchy needed to sequence implementation work.
- Existing BitNet broker work provides a realistic starting point for local-first harness evolution.

---

### Dependencies

| Dependency | Type |
|------------|------|
| [PS-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/PS-LAH-001_project_scope.md) | Blocker |
| [docs/plans/local_llm_agent_harness_modern_stacks.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/local_llm_agent_harness_modern_stacks.md) | Artifact |
| Confirmed GitHub Project 2 fields for status, parent issue, size, and priority | Artifact |

---

### Out of Scope

- Shipping a full end-user product experience on top of the harness
- Supporting every external provider feature in the first milestone

---

### Artifacts

- [ ] Figma / Design Comps: N/A
- [x] Workflow Diagram: [local_llm_agent_harness_modern_stacks.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/local_llm_agent_harness_modern_stacks.md)
- [x] Issue-ready planning drafts: [artifacts folder](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/README.md)

---

### I Know I Am Done When

- [ ] The Initiative has a complete Epic, Story, and Task hierarchy with dependencies.
- [ ] The work is sequenced so the runtime core lands before adapters, control planes, and readiness work.
- [ ] The hierarchy is ready to copy into GitHub Project 2 with issue types, labels, parents, and blocked-by links.

---

### Epics

| Order | # | Epic Title | Description | Points | Hours | Dependencies | QA Can Test |
|-------|---|------------|-------------|--------|-------|--------------|-------------|
| 1 | EP-LAH-001 | Runtime Core and Context Compiler | Establish the canonical runtime model, session ledger, and context compiler. | 13 | 56 | None | Yes |
| 2 | EP-LAH-002 | Provider Adapters and Tool Broker | Add adapter translation and a unified tool/MCP broker boundary. | 13 | 56 | EP-LAH-001 | Yes |
| 3 | EP-LAH-003 | Memory Workflow and Policy Controls | Add memory, workflow orchestration, specialists, and policy boundaries. | 13 | 56 | EP-LAH-001, EP-LAH-002 | Yes |
| 4 | EP-LAH-004 | Observability and Modern Stack Readiness | Add tracing, evals, VS Code integration, docs, and UAT for rollout readiness. | 13 | 44 | EP-LAH-001, EP-LAH-002, EP-LAH-003 | Yes |
| | | | **Total** | **52** | **212** | | |

> **Sizing Matrix**: Points use Fibonacci values.

**Sequence & Sizing Rationale:**
- Development efficiency: runtime and context contracts land first so later epics share one foundation.
- Risk reduction: adapters and tool brokering are split from memory/workflow so interface instability is reduced early.
- Value delivery: each epic produces a testable slice of harness capability that builds toward a usable local agent runtime.

---

### Questions for Tech Lead

- What contract details should be frozen before adapter implementation begins?
- Which provider adapters are must-have in the first implementation milestone?
- What minimum tracing/eval set is required before broader internal adoption?

---

## ⚙️ TECH LEAD SECTION

### Impacted Functional Areas

| Functional Area | Impact Level | Primary Files | Notes |
|-----------------|--------------|---------------|-------|
| Broker runtime | High | `broker/`, `run_broker.py` | Existing broker evolves into harness foundation |
| Prompt/context assembly | High | `broker/prompting.py`, session state code | Canonical compilation boundary |
| Tooling/MCP | High | `broker/tools.py`, `broker/mcp*.py` | Unified descriptor and policy model |
| Observability/UAT | Medium | `broker/turn_trace.py`, `monitor_broker_debug.py`, `run_conversation_uat.py` | Readiness and operational validation |

---

### High-Level Technical Notes

- The design should preserve audit fidelity in the ledger while shaping model-facing context separately.
- Provider-specific transport artifacts should not become the durable internal memory model.

---

### Epic Refinement Notes

- Epic 1 must finish enough contract work to unblock all downstream epics.
- Epic 4 should not start until at least one end-to-end adapter and one governed tool path exist.

---

_Created: 2026-03-21_
_Product Owner: Chris Kreager_
_Tech Lead: TBD_
