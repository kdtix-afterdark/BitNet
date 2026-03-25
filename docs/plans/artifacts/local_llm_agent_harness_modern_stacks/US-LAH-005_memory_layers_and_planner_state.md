# User Story: US-LAH-005 Implement hot warm cold memory and planner state

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `memory`, `planner`
> **Blocks**: US-LAH-006, US-LAH-007, US-LAH-008
> **Blocked By**: US-LAH-002, US-LAH-004

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-003_memory_workflow_and_policy_controls.md)  
> **Size**: L (8 pts / 24-40 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want the harness to use layered memory and explicit planner state,
So that long-running work can preserve the right information without replaying one giant transcript.
```

---

### TL;DR

Split continuity into memory layers and represent planning explicitly instead of relying on hidden reasoning or raw transcript replay.

---

### Why This Matters

The plan recommends hot, warm, and cold memory plus explicit planner state. That keeps continuity durable and auditable while reducing prompt bloat and provider-specific reasoning dependencies.

---

### Assumptions

- **Roles**: Platform engineer, memory/workflow maintainer
- **Starting point**: Ledger and context compiler are available
- **Preconditions**: Tool and adapter seams are defined enough to supply evidence and artifacts

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-002_session_ledger_and_context_compiler.md) | Ledger and compiler boundary | Blocked |
| [US-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-004_tool_broker_and_mcp_translation.md) | Tool evidence model | Blocked |

---

### I Know I Am Done When

- [ ] Hot, warm, and cold memory responsibilities are defined clearly.
- [ ] Planner state is represented explicitly and can reference evidence and open questions.
- [ ] The story defines what to persist versus what to keep transport-specific.
- [ ] Workflow stories can consume planner state and memory without re-architecting continuity.

---

### Acceptance Criteria

**Scenario 1**: Layered continuity
- **Given**: a long-running harness session
- **When**: continuity needs are reviewed
- **Then**: working context, summaries/checkpoints, and durable facts are assigned to separate memory layers

**Scenario 2**: Explicit planning
- **Given**: a task requiring multi-step execution
- **When**: the harness captures planning state
- **Then**: assumptions, evidence, next actions, and open questions are represented explicitly

**Scenario 3**: Provider independence
- **Given**: provider-specific reasoning artifacts
- **When**: memory persistence is designed
- **Then**: durable memory stores explicit planning and facts instead of hidden provider reasoning

---

### Constraints

- Do not store one giant rolling transcript as the sole memory model
- Do not persist hidden reasoning as durable planner state

---

### Questions for Engineering

- What qualifies for warm memory versus planner state?
- Which memory writes should happen automatically versus through workflow steps?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Extend current summary/checkpoint flow only | 8 pts / 24-40 hrs | Fastest. Weak planner semantics. |
| B | Add a dedicated planner object plus layered memory selectors | 8 pts / 24-40 hrs | Strong model. More design work. |
| C | Use provider-native memory features where available | 8 pts / 24-40 hrs | Less custom work. Too provider-specific. |

**Recommended**: B because it preserves provider neutrality while supporting durable continuity.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| ⚙️ Backend | Y | [TASK-LAH-009](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-009_memory_layer_contract_and_retention_rules.md) | 4 |
| ⚙️ Backend | Y | [TASK-LAH-010](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-010_planner_state_checkpointing_and_memory_selection.md) | 4 |
| 🧪 Test/Verify | Y | Validate continuity and compaction rules | 3 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Durable state | `broker/durable_state.py` | Checkpoints and summaries |
| Module | Memory routing | `broker/memory_routing.py` | Retrieval and persistence |

---

### Regression Risk

- [ ] Summary and compaction behavior
- [ ] Memory recall and planner continuity

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
