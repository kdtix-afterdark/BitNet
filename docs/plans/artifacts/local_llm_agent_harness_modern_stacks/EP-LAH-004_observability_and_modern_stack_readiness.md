# Epic: EP-LAH-004 Observability and Modern Stack Readiness

> **Issue Type**: Epic
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Repository**: `kdtix-afterdark/BitNet`
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `observability`, `evals`, `uat`
> **Parent Initiative**: [INIT-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/INIT-LAH-001_initiative.md)
> **Blocks**: US-LAH-007, US-LAH-008, US-LAH-009
> **Blocked By**: EP-LAH-001, EP-LAH-002, EP-LAH-003

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

Make the harness observable, measurable, and ready for structured rollout across modern stacks.

### Release Value

After this epic, the team can see what the harness is doing, evaluate its behavior, validate real-world scenarios before wider adoption, and exercise a supported VS Code Chat surface that can remain useful long term.

### Success Criteria

- [ ] Runs emit enough trace and audit data to diagnose failures and compare behavior.
- [ ] The team has concrete UAT scenarios for modern-stack validation.
- [ ] VS Code can serve as a supported UAT and daily-use client surface through a productized integration path.
- [ ] Rollout readiness is supported by issue-ready evidence, not intuition.

---

### Feature Scope

| # | Feature/Capability | What It Includes | What It Enables |
|---|-------------------|------------------|-----------------|
| 1 | Tracing and audit | Model, tool, memory, approval, and workflow spans | Root-cause diagnosis |
| 2 | Evaluation hooks | Regression fixtures and eval entry points | Repeatable quality checks |
| 3 | VS Code integration surface | Productized VS Code model-provider path against a standardized broker endpoint | Daily-use validation in the primary editor |
| 4 | Readiness validation | Docs, run profiles, UAT, rollout checklist | Safer adoption |

---

### Assumptions

- Readiness work depends on core runtime, adapters, and control planes existing at least in draft form.
- The current broker/UAT work provides a usable starting point for observability design.
- True BitNet UAT requires the local Apple Silicon plus Metal runtime path; GitHub-hosted and cloud execution can support planning, review, and limited CPU-only verification but not the authoritative local-model experience.

---

### Dependencies

| Dependency | Type | Owner | Status |
|------------|------|-------|--------|
| EP-LAH-001 | Blocker | Chris Kreager | Draft |
| EP-LAH-002 | Blocker | Chris Kreager | Draft |
| EP-LAH-003 | Blocker | Chris Kreager | Draft |

---

### Out of Scope

- Broad external rollout beyond internal validation
- Production analytics beyond harness-focused tracing and evaluation

---

### Artifacts

- [ ] Figma / Jira Comps: N/A
- [x] Workflow Diagram: [local_llm_agent_harness_modern_stacks.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/local_llm_agent_harness_modern_stacks.md)
- [ ] [Other artifacts]

---

### I Know I Am Done When

- [ ] There is a clear tracing and eval plan tied to concrete delivery stories.
- [ ] The team has a defined VS Code Chat integration path that can be used for repeatable UAT.
- [ ] Modern-stack UAT is defined well enough to validate the harness after implementation.
- [ ] The team can map readiness evidence back to GitHub Project items.

---

### User Stories

| Order | # | Story Title | Description | Points | Hours | Dependencies | QA Can Test |
|-------|---|-------------|-------------|--------|-------|--------------|-------------|
| 1 | US-LAH-007 | Emit tracing eval and audit spans | Define and capture the operational signals needed to observe the harness. | 5 | 16 | EP-LAH-001, EP-LAH-002, EP-LAH-003 | Yes |
| 2 | US-LAH-009 | Enable productized VS Code Chat integration through a Responses-compatible BitNet provider | Add a supported VS Code model-provider path for long-term UAT and daily local use. | 5 | 20 | US-LAH-003, US-LAH-004, US-LAH-007 | Yes |
| 3 | US-LAH-008 | Deliver readiness docs and UAT for modern stacks | Package the run profiles, rollout checklist, and UAT plan for adoption, including VS Code validation. | 3 | 8 | US-LAH-007, US-LAH-009 | Yes |
| | | | **Total** | **13** | **44** | | |

**Sequence & Sizing Rationale:**
- Development efficiency: observability design comes before final readiness validation.
- Risk reduction: traces and eval hooks surface failures before UAT and rollout.
- Value delivery: VS Code integration lands before final readiness packaging so the team can validate in the editor they use most.

---

### Questions for Tech Lead

- Which spans and events are mandatory for day-one operational support?
- What is the smallest UAT set that proves modern-stack readiness credibly?
- Which VS Code model-provider path and version range should be treated as the supported long-term target?

---

## ⚙️ TECH LEAD SECTION

### Impacted Functional Areas

| Functional Area | Impact Level | Primary Files | Notes |
|-----------------|--------------|---------------|-------|
| Trace pipeline | High | `broker/turn_trace.py`, log/monitor utilities | Operational evidence |
| Eval harness | Medium | UAT and verification scripts | Repeatable quality checks |
| Documentation | Medium | `README.md`, run profiles, planning docs | Adoption support |

---

### High-Level Technical Notes

- Observability should follow the canonical event model, not ad hoc logs per subsystem.
- UAT should validate provider flexibility, tool governance, memory continuity, restart behavior, and the supported VS Code Chat path.
- The authoritative UAT path for BitNet-backed scenarios remains local execution on Metal-capable hardware, while cloud or GitHub-hosted validation should be treated as secondary CPU-only verification.

---

### Code Areas to Examine

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Turn tracing | `broker/turn_trace.py` | Per-turn artifacts |
| Script | UAT runner | `run_conversation_uat.py` | Realistic scenario execution |
| Script | Debug monitor | `monitor_broker_debug.py` | Live analysis support |

---

### Database Considerations

| Change Type | Object | Migration Script Needed |
|-------------|--------|------------------------|
| N/A | N/A | No |

---

### Shared Components

- Trace taxonomy: Used in Stories US-LAH-007, US-LAH-009, and US-LAH-008

---

### Technical Dependencies

| System/API | What's Needed | Status |
|------------|---------------|--------|
| Broker trace stream | Event output for monitoring | Available |
| UAT harness | Scenario execution surface | Available |
| VS Code model-provider path | Supported client surface | Planned |

---

### Cross-Area Impacts

| Area | Why It May Be Impacted | Mitigation |
|------|----------------------|------------|
| Workflow and memory | Spans must cover retries, memory hits, and approvals | Design trace taxonomy with shared identifiers |

---

### Potential Conflicts

- Over-logging could create noise if trace taxonomy is not bounded well.

---

### Performance Considerations

- Trace capture should remain useful without overwhelming the runtime or operators.

---

### Security/Compliance

- Audit output must not leak secrets or hidden operational data into user-facing channels.

---

### Regression Risk Areas

- [ ] Trace correctness and correlation IDs
- [ ] UAT state capture
- [ ] Rollout checklist completeness

---

### Spike Needed?

- [ ] Yes - [What needs investigation before starting]
- [x] No

---

_Last Updated: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Technical Analysis By: Codex_
