# User Story: US-LAH-008 Deliver readiness docs and UAT for modern stacks

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `uat`, `readiness`, `documentation`
> **Blocks**: None
> **Blocked By**: US-LAH-003, US-LAH-004, US-LAH-006, US-LAH-007, US-LAH-009

> Jira Level 4 — smallest unit of deliverable work, sits under an Epic.
> See [PRODUCT_GUIDE.md](../PRODUCT_GUIDE.md) for guidance.
> **Keep the PRODUCT SECTION business-focused** — no technical jargon, implementation details, system internals, or code references. Those belong in the Engineering section.

---

> **Status**: Draft  
> **Priority**: High  
> **Parent Epic**: [EP-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-004_observability_and_modern_stack_readiness.md)  
> **Size**: S (3 pts / 8-16 hrs)

---

## 📋 PRODUCT SECTION

### User Story

```
As a platform engineer,
I want issue-ready readiness docs and realistic UAT scenarios for the harness,
So that the team can validate modern-stack behavior before wider adoption.
```

---

### TL;DR

Package the run profiles, rollout checklist, and UAT plan needed to verify the harness on modern stacks.

---

### Why This Matters

The plan is architectural, but the team still needs a practical readiness package. That includes run profiles, constraints, UAT scenarios, and a checklist that connects architecture decisions to observable evidence.

The readiness package also needs to separate true local BitNet validation from what GitHub-hosted or cloud CPU environments can reasonably verify, so the backlog does not promise a test path the runtime cannot support.

---

### Assumptions

- **Roles**: Platform engineer, tester, reviewer
- **Starting point**: Observability and control-plane stories define the runtime behavior to validate
- **Preconditions**: Trace and eval hooks exist for evidence capture

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-003_provider_adapter_layer.md) | Adapter readiness | Blocked |
| [US-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-004_tool_broker_and_mcp_translation.md) | Tool/MCP readiness | Blocked |
| [US-LAH-006](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-006_workflow_orchestration_and_approvals.md) | Workflow and policy readiness | Blocked |
| [US-LAH-007](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-007_tracing_evals_and_audit_spans.md) | Observability readiness | Blocked |
| [US-LAH-009](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-009_vscode_chat_integration_via_responses_provider.md) | VS Code Chat validation surface | Blocked |

---

### I Know I Am Done When

- [ ] Modern-stack run profiles and assumptions are documented.
- [ ] UAT scenarios cover backend flexibility, tools, memory, workflow, approval behavior, and the supported VS Code Chat surface.
- [ ] Rollout readiness can be judged from concrete evidence instead of ad hoc testing.
- [ ] The story output is ready to inform GitHub Project execution and review.

---

### Acceptance Criteria

**Scenario 1**: Run profile readiness
- **Given**: a modern-stack target environment
- **When**: the team reviews the story output
- **Then**: the expected runtime profile and constraints are documented clearly

**Scenario 2**: UAT scenario completeness
- **Given**: a tester preparing validation
- **When**: they use the story output
- **Then**: they have repeatable scenarios with prerequisites, steps, expected outcomes, and a VS Code execution path where required

**Scenario 3**: Rollout evidence
- **Given**: the team considers broader use of the harness
- **When**: they inspect readiness materials
- **Then**: they can point to trace, eval, and UAT evidence supporting adoption

---

### Constraints

- Do not treat informal smoke tests as sufficient UAT
- Do not declare readiness without observable evidence from the harness
- Do not claim GitHub-hosted or generic cloud validation is equivalent to the authoritative local Metal-backed BitNet UAT path

---

### Questions for Engineering

- Which modern-stack environments are in-scope for first validation?
- What is the smallest UAT set that still proves the architecture credibly?
- Which checks belong in GitHub or cloud CPU environments, and which must remain local-only?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Focus on docs only | 3 pts / 8-16 hrs | Fastest. Weak validation story. |
| B | Docs plus realistic UAT matrix and checklist | 3 pts / 8-16 hrs | Best readiness value. Slightly more coordination. |
| C | Full automated validation suite before docs | 3 pts / 8-16 hrs | Strong long term. Too much for first readiness pass. |

**Recommended**: B because it balances readiness evidence with achievable planning scope.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| 🖥️ UI | N | N/A | 0 |
| ⚙️ Backend | Y | [TASK-LAH-015](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-015_modern_stack_docs_and_run_profiles.md) | 3 |
| 🔍 Research/Spike | Y | [TASK-LAH-020](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-020_clean_lab_bootstrap_and_gguf_dependency_spike.md) | 4 |
| 🧪 Test/Verify | Y | [TASK-LAH-016](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-016_end_to_end_uat_and_readiness_checklist.md) | 4 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Plan | Harness plan | `docs/plans/local_llm_agent_harness_modern_stacks.md` | Source narrative |
| Scripts | UAT and debug tooling | `run_conversation_uat.py`, `monitor_broker_debug.py` | Validation assets |

---

### Regression Risk

- [ ] Incomplete UAT coverage
- [ ] Missing rollout evidence

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD_
