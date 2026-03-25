# User Story: US-LAH-007 Emit tracing eval and audit spans

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `tracing`, `evals`, `audit`
> **Blocks**: US-LAH-008
> **Blocked By**: US-LAH-002, US-LAH-004, US-LAH-006

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-004_observability_and_modern_stack_readiness.md)  
> **Size**: M (5 pts / 16-24 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want the harness to emit consistent traces, eval hooks, and audit artifacts,
So that failures can be diagnosed and behavior can be measured before rollout.
```

---

### TL;DR

Define and emit the operational signals needed to understand harness behavior across model, tool, memory, workflow, and approval events.

---

### Why This Matters

The plan calls out tracing and evals as first-class concerns. Without them, the harness may work in isolated demos but remain hard to debug, compare, or trust during real usage.

---

### Assumptions

- **Roles**: Platform engineer, operator, evaluator
- **Starting point**: Core runtime, tool broker, and workflow seams exist
- **Preconditions**: There are stable event identifiers to correlate spans

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-002](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-002_session_ledger_and_context_compiler.md) | Core event flow | Blocked |
| [US-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-004_tool_broker_and_mcp_translation.md) | Tool signals | Blocked |
| [US-LAH-006](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-006_workflow_orchestration_and_approvals.md) | Workflow and approval signals | Blocked |

---

### I Know I Am Done When

- [ ] There is a canonical span/event taxonomy for the harness.
- [ ] Model, tool, memory, approval, and workflow boundaries are represented in trace design.
- [ ] Eval and audit outputs can be tied back to the same run/session identity.
- [ ] Readiness and UAT work can consume these signals.

---

### Acceptance Criteria

**Scenario 1**: Trace taxonomy
- **Given**: a harness run with model and tool activity
- **When**: traces are reviewed
- **Then**: the event taxonomy captures the key boundaries consistently

**Scenario 2**: Eval hook readiness
- **Given**: a future regression or UAT scenario
- **When**: the harness is evaluated
- **Then**: the design provides a clear hook for measuring outcomes

**Scenario 3**: Audit continuity
- **Given**: a run that requires later review
- **When**: audit artifacts are examined
- **Then**: the relevant runtime events can be correlated cleanly

---

### Constraints

- Do not make tracing so verbose that it obscures the real signal
- Do not leak secrets or hidden reasoning into audit output

---

### Questions for Engineering

- Which spans are mandatory in milestone one?
- What should be captured in eval fixtures versus audit artifacts?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Extend current logging only | 5 pts / 16-24 hrs | Fastest. Weak structure for evals. |
| B | Build canonical trace events and attach eval hooks | 5 pts / 16-24 hrs | Stronger architecture. More up-front design. |
| C | Defer evals until after rollout | 5 pts / 16-24 hrs | Lower immediate cost. Higher rollout risk. |

**Recommended**: B because observability is part of the target architecture, not a postscript.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| ⚙️ Backend | Y | [TASK-LAH-013](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-013_trace_taxonomy_and_span_emission.md) | 4 |
| 🧪 Test/Verify | Y | [TASK-LAH-014](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-014_eval_hooks_and_audit_artifact_capture.md) | 4 |
| 🧪 Test/Verify | Y | Validate trace usefulness against realistic UAT flows | 2 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Turn trace recorder | `broker/turn_trace.py` | Core event output |
| Script | Debug monitor | `monitor_broker_debug.py` | Live trace consumption |

---

### Regression Risk

- [ ] Correlation IDs and event linkage
- [ ] Trace noise versus signal quality

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
