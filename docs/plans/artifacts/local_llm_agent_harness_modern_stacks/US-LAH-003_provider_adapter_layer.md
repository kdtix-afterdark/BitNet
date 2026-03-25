# User Story: US-LAH-003 Implement provider adapter layer with Responses-compatible first delivery

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `adapters`
> **Blocks**: US-LAH-004, US-LAH-008
> **Blocked By**: US-LAH-001

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-002_provider_adapters_and_tool_broker.md)  
> **Size**: M (5 pts / 16-24 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want provider adapters that translate the harness turn model into different backend shapes,
So that the harness can support hosted and local model stacks without duplicating orchestration logic.
```

---

### TL;DR

Build the translation boundary between the canonical turn model and multiple model providers or local backends, starting with a Responses-compatible target.

---

### Why This Matters

The plan explicitly recommends adapter translation instead of locking the system to one provider’s message format. For this team, Responses-compatible transport is the best first target because it aligns with Codex and local Responses-compatible endpoints, while later adapter work can still prove portability.

---

### Assumptions

- **Roles**: Platform engineer, adapter maintainer
- **Starting point**: Canonical contracts are approved
- **Preconditions**: Runtime core story is available

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-001_canonical_runtime_contracts_and_run_profiles.md) | Shared contract definitions | Blocked |

---

### I Know I Am Done When

- [ ] The harness has a provider-neutral adapter interface.
- [ ] The first concrete adapter target is Responses-compatible transport.
- [ ] The follow-on adapter order is documented as MCP-facing broker work first, Anthropic next, and native fallback only if still needed.
- [ ] Provider-specific artifacts stay within adapters instead of leaking into shared runtime contracts.
- [ ] Later stories can target the adapter interface instead of raw provider APIs.

---

### Acceptance Criteria

**Scenario 1**: Shared adapter contract
- **Given**: a harness turn and run profile
- **When**: the system selects a backend
- **Then**: the adapter translates that turn through one shared interface

**Scenario 2**: Responses-first implementation
- **Given**: the team’s primary use of Codex and local Responses-compatible endpoints
- **When**: the first adapter slice is selected
- **Then**: Responses-compatible transport is implemented before Anthropic or native fallback-specific work

**Scenario 3**: Provider separation
- **Given**: different backend shapes
- **When**: the story output is reviewed
- **Then**: transport-specific concerns are confined to adapter responsibilities

**Scenario 4**: Deferred fallback work
- **Given**: a local backend that can already sit behind a Responses-compatible surface
- **When**: the adapter roadmap is reviewed
- **Then**: native local fallback remains deferred until a real compatibility gap is proven

---

### Constraints

- Do not duplicate business logic inside adapters
- Do not persist provider-specific thinking artifacts as durable internal state

---

### Questions for Engineering

- Which backend capability differences belong in the adapter versus the run profile?
- What evidence is required before creating a dedicated native local fallback adapter?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | One generic adapter with mode flags | 5 pts / 16-24 hrs | Smaller surface. Can become muddy fast. |
| B | Separate adapter modules per provider/backend family | 5 pts / 16-24 hrs | Clearer boundaries. Slightly more boilerplate. |
| C | Hybrid shared base plus provider-specific translators | 5 pts / 16-24 hrs | Reuse with good isolation. Needs disciplined interfaces. |

**Recommended**: C because it balances explicit provider translation with shared harness behavior while still allowing a Responses-first rollout.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| 🔍 Research/Spike | Y | [TASK-LAH-005](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-005_adapter_interface_and_capability_translator.md) | 3 |
| ⚙️ Backend | Y | [TASK-LAH-006](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-006_responses_anthropic_and_local_adapter_implementation.md) | 4 |
| 🧪 Test/Verify | Y | Validate representative request/response translation paths | 2 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Runtime transport | `broker/llama_runtime.py` | Local target today |
| Module | Future adapters | `broker/` | Provider translation boundary |

---

### Regression Risk

- [ ] Request translation drift
- [ ] Capability mismatch between run profiles and adapters
- [ ] Overbuilding a native local fallback path before it is justified

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
