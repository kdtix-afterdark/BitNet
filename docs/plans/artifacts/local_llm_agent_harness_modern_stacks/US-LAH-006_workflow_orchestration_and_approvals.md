# User Story: US-LAH-006 Separate workflow orchestration from turn execution and approvals

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `workflow`, `approvals`, `sandbox`
> **Blocks**: US-LAH-007, US-LAH-008
> **Blocked By**: US-LAH-005

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-003_memory_workflow_and_policy_controls.md)  
> **Size**: M (5 pts / 16-24 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want durable workflow orchestration, specialist routing, and approval boundaries outside the single-turn loop,
So that the harness can retry, resume, and govern work safely.
```

---

### TL;DR

Separate job-level execution from single-turn model behavior and put approvals and sandboxing at the broker boundary.

---

### Why This Matters

The plan recommends two loops: one for model turns and one for durable workflow control. It also recommends treating specialists as bounded tools or handoffs and enforcing policy outside the model prompt. Without that, long-running work becomes brittle and unsafe.

---

### Assumptions

- **Roles**: Platform engineer, workflow owner
- **Starting point**: Memory layers and planner state exist
- **Preconditions**: Tool broker metadata includes side effects and approval-relevant signals

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-005](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-005_memory_layers_and_planner_state.md) | Memory and planner foundation | Blocked |

---

### I Know I Am Done When

- [ ] The team can describe the turn loop separately from the workflow loop.
- [ ] Specialist execution is framed as tools or bounded handoffs, not free-floating agents.
- [ ] Approvals and sandboxing sit at the broker boundary instead of inside prompt text.
- [ ] Retry, timeout, and resume concerns have a durable execution home.

---

### Acceptance Criteria

**Scenario 1**: Workflow separation
- **Given**: a long-running agent task
- **When**: orchestration is reviewed
- **Then**: job-level control is separated from per-turn model execution

**Scenario 2**: Specialist routing
- **Given**: a specialist subtask
- **When**: the workflow plans execution
- **Then**: the specialist is modeled as a bounded handoff or tool with constrained permissions

**Scenario 3**: Approval enforcement
- **Given**: a mutating action
- **When**: it reaches execution
- **Then**: approval and sandbox policy are enforced outside the model prompt

---

### Constraints

- Do not allow unrestricted autonomy by default
- Do not make approval state implicit in chat history alone

---

### Questions for Engineering

- Which workflow steps should stay deterministic in code?
- What is the default approval behavior for read-only versus mutating operations?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Keep orchestration inside the broker turn path | 5 pts / 16-24 hrs | Simple. Harder to resume and govern. |
| B | Add a durable workflow layer around the turn engine | 5 pts / 16-24 hrs | Better control. Slightly more moving parts. |
| C | Split workflow and specialist routing into separate services immediately | 5 pts / 16-24 hrs | Clean separation. Too much early scope. |

**Recommended**: B because it matches the target design without over-expanding the first milestone.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| ⚙️ Backend | Y | [TASK-LAH-011](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-011_workflow_engine_separation_and_job_semantics.md) | 4 |
| ⚙️ Backend | Y | [TASK-LAH-012](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-012_approval_sandbox_and_specialist_routing.md) | 4 |
| 🧪 Test/Verify | Y | Validate approval paths and resume semantics | 3 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Broker runtime | `broker/server.py` | Current turn loop |
| Module | Policy controls | Broker config and tool metadata | Sandbox and approvals |

---

### Regression Risk

- [ ] Approval leaks
- [ ] Retry/resume behavior

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
