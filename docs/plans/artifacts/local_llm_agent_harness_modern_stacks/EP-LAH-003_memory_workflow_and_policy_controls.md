# Epic: EP-LAH-003 Memory Workflow and Policy Controls

> **Issue Type**: Epic
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Repository**: `kdtix-afterdark/BitNet`
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `memory`, `workflow`, `policy`
> **Parent Initiative**: [INIT-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/INIT-LAH-001_initiative.md)
> **Blocks**: EP-LAH-004, US-LAH-005, US-LAH-006
> **Blocked By**: EP-LAH-001, EP-LAH-002

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

Give the harness durable memory, workflow control, specialist boundaries, and approval policy so it can operate safely and resume work reliably.

### Release Value

After this epic, the harness can hold the right information in the right layer, manage long-running work beyond a single model turn, and keep mutations and sensitive actions behind policy checks.

### Success Criteria

- [ ] Memory is split into hot, warm, and cold layers with clear responsibility.
- [ ] Workflow orchestration is distinct from single-turn model execution.
- [ ] Approval and sandbox policy are applied at the broker boundary, not left to prompt text alone.

---

### Feature Scope

| # | Feature/Capability | What It Includes | What It Enables |
|---|-------------------|------------------|-----------------|
| 1 | Memory layering | Hot, warm, cold memory plus summaries and checkpoints | Longer-running continuity |
| 2 | Workflow engine | Retries, resumptions, orchestration, specialists | Durable execution beyond one turn |
| 3 | Policy controls | Approvals, sandboxing, scoped permissions | Safer operations |

---

### Assumptions

- Adapter and tool broker contracts exist before policy and workflow are finalized.
- The harness will need both short-turn execution and durable job semantics.

---

### Dependencies

| Dependency | Type | Owner | Status |
|------------|------|-------|--------|
| EP-LAH-001 | Blocker | Chris Kreager | Draft |
| EP-LAH-002 | Blocker | Chris Kreager | Draft |

---

### Out of Scope

- Full enterprise IAM implementation
- Unlimited autonomous execution without approvals

---

### Artifacts

- [ ] Figma / Jira Comps: N/A
- [x] Workflow Diagram: [local_llm_agent_harness_modern_stacks.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/local_llm_agent_harness_modern_stacks.md)
- [ ] [Other artifacts]

---

### I Know I Am Done When

- [ ] Memory, workflow, and approvals are no longer implicit transcript behavior.
- [ ] The epic’s stories define how continuity and governance work together.
- [ ] The resulting plan supports restart-safe and policy-aware execution.

---

### User Stories

| Order | # | Story Title | Description | Points | Hours | Dependencies | QA Can Test |
|-------|---|-------------|-------------|--------|-------|--------------|-------------|
| 1 | US-LAH-005 | Implement hot warm cold memory and planner state | Model durable continuity and explicit planning state. | 8 | 36 | EP-LAH-001, EP-LAH-002 | Yes |
| 2 | US-LAH-006 | Separate workflow orchestration from turn execution and approvals | Add the workflow loop, specialists, approvals, and sandbox boundaries. | 5 | 20 | US-LAH-005 | Yes |
| | | | **Total** | **13** | **56** | | |

**Sequence & Sizing Rationale:**
- Development efficiency: memory and planner state come first because workflow uses them.
- Risk reduction: policy boundaries are designed with workflow orchestration, not added later.
- Value delivery: the epic creates the control plane needed for practical agent operation.

---

### Questions for Tech Lead

- What information belongs in warm memory versus explicit planner state?
- Which workflows should remain code-driven versus model-directed in the first milestone?

---

## ⚙️ TECH LEAD SECTION

### Impacted Functional Areas

| Functional Area | Impact Level | Primary Files | Notes |
|-----------------|--------------|---------------|-------|
| Durable state and memory | High | `broker/durable_state.py`, memory routing modules | Continuity and checkpoints |
| Workflow control | High | Broker orchestration and future workflow modules | Job-level execution |
| Policy boundary | High | Approval and sandbox controls | Safety-critical |

---

### High-Level Technical Notes

- Planner state should be explicit and auditable instead of relying on hidden reasoning.
- Workflow orchestration should remain deterministic where retries, approvals, and resumptions matter most.

---

### Code Areas to Examine

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Durable state | `broker/durable_state.py` | Checkpoints and compaction |
| Module | Memory routing | `broker/memory_routing.py` | Memory selection and retrieval |
| Module | Broker runtime | `broker/server.py` | Approval and orchestration seams |

---

### Database Considerations

| Change Type | Object | Migration Script Needed |
|-------------|--------|------------------------|
| Data Model | Memory/checkpoint structures | No |

---

### Shared Components

- Planner state object: Used in Stories US-LAH-005 and US-LAH-006

---

### Technical Dependencies

| System/API | What's Needed | Status |
|------------|---------------|--------|
| Memory layer | Durable memory and summary storage | Partially available |
| Tool broker | Policy-aware tool metadata | Planned |

---

### Cross-Area Impacts

| Area | Why It May Be Impacted | Mitigation |
|------|----------------------|------------|
| Observability | Workflow and approvals must emit traceable events | Design spans alongside control plane |

---

### Potential Conflicts

- Workflow autonomy choices may conflict with tighter approval requirements.

---

### Performance Considerations

- Memory retrieval and checkpoint compaction should avoid turning every run into a transcript replay.

---

### Security/Compliance

- Mutating tools and remote access paths must remain behind explicit approval and sandbox controls.

---

### Regression Risk Areas

- [ ] Restart and resume behavior
- [ ] Memory selection and compaction
- [ ] Approval enforcement

---

### Spike Needed?

- [x] Yes - workflow/policy boundaries and memory retention need targeted validation
- [ ] No

---

_Last Updated: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Technical Analysis By: Codex_
