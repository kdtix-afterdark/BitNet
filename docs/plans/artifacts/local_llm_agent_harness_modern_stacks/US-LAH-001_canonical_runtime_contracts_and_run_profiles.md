# User Story: US-LAH-001 Define canonical runtime contracts and run profiles

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `runtime`
> **Blocks**: US-LAH-002, US-LAH-003
> **Blocked By**: None

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-001_runtime_core_context_compiler.md)  
> **Size**: M (5 pts / 16-24 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want one canonical contract set for runtime events and run profiles,
So that the harness can target multiple backends without redesigning its core model.
```

---

### TL;DR

Define the internal language the harness uses before any provider-specific translation happens.

---

### Why This Matters

The plan makes clear that the system should compile into provider-specific requests instead of mirroring any one transcript format. Without shared contracts, every adapter and workflow feature will drift and the harness will become harder to evolve.

---

### Assumptions

- **Roles**: Platform engineer, agent runtime maintainer
- **Starting point**: Existing broker/runtime concepts already exist in the repo
- **Preconditions**: Epic EP-LAH-001 is active

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| None | N/A | None |

---

### I Know I Am Done When

- [ ] Canonical `Event`, `RunProfile`, `ToolDescriptor`, and `TurnResult` shapes are documented.
- [ ] Run profiles capture model family, tool policy, sandbox, and budget intent.
- [ ] Provider-specific behavior is clearly separated from internal contracts.
- [ ] Downstream stories can reference these contracts without redefining them.

---

### Acceptance Criteria

**Scenario 1**: Shared contract review
- **Given**: the harness plan and current broker behavior
- **When**: the team reviews the story output
- **Then**: there is one agreed contract set for runtime events and run profiles

**Scenario 2**: Adapter readiness
- **Given**: a future provider adapter story
- **When**: it consumes the story output
- **Then**: it can map from the internal contracts instead of inventing new ones

**Scenario 3**: Planning continuity
- **Given**: later stories in this initiative
- **When**: they reference runtime objects
- **Then**: they use the same contract vocabulary consistently

---

### Constraints

- Do not lock the design to a single provider’s transcript model
- Do not treat hidden reasoning as a durable contract surface

---

### Questions for Engineering

- Which contract fields are mandatory in milestone one?
- Which fields can remain optional until adapter implementation?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Define contracts in markdown first, then code | 5 pts / 16-24 hrs | Clear review path. Slower to validate in code. |
| B | Define contracts directly in code types | 5 pts / 16-24 hrs | Fast feedback. Easier to miss product-readable context. |
| C | Hybrid docs plus code types | 5 pts / 16-24 hrs | Best alignment. Slightly more coordination. |

**Recommended**: C because the issue hierarchy and later implementation both need the same shared contract language.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| 🔍 Research/Spike | Y | [TASK-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-001_event_turnresult_and_visibility_contracts.md) | 3 |
| ⚙️ Backend | Y | [TASK-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-002_run_profile_and_capability_matrix.md) | 4 |
| 🧪 Test/Verify | Y | Review contract applicability across planned adapters | 2 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Prompt/runtime seams | `broker/` | Contract consumers |
| Plan | Harness architecture | `docs/plans/local_llm_agent_harness_modern_stacks.md` | Source guidance |

---

### Regression Risk

- [ ] Contract drift between planning docs and implementation
- [ ] Provider-specific assumptions leaking into shared types

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
