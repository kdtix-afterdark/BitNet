# Epic: EP-LAH-001 Runtime Core and Context Compiler

> **Issue Type**: Epic
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Repository**: `kdtix-afterdark/BitNet`
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `runtime`, `context-compiler`
> **Parent Initiative**: [INIT-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/INIT-LAH-001_initiative.md)
> **Blocks**: EP-LAH-002, EP-LAH-003, EP-LAH-004, US-LAH-001, US-LAH-002
> **Blocked By**: INIT-LAH-001

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

Define the harness’s core runtime language so the team stops treating the raw transcript as the product boundary. This epic gives every later capability one shared way to represent session state, run intent, and model-facing context.

### Release Value

After this epic, the team can build on a stable core instead of reinventing prompt assembly and session state per provider or per feature.

### Success Criteria

- [ ] The harness has agreed canonical contracts for runtime events and turn results.
- [ ] Session state is represented as a ledger instead of only a rolling transcript.
- [ ] Context is compiled intentionally for the model rather than replayed naively.

---

### Feature Scope

| # | Feature/Capability | What It Includes | What It Enables |
|---|-------------------|------------------|-----------------|
| 1 | Canonical contracts | Event, run profile, tool descriptor, turn result definitions | Provider-neutral implementation planning |
| 2 | Session ledger | Append-only event model and visibility rules | Restart-safe and auditable state |
| 3 | Context compiler | Model-facing request assembly from structured state | Consistent prompts across runtime modes |

---

### Assumptions

- Existing broker traces and durable state work provide enough evidence to define the first contract set.
- This epic can deliver value before any full provider adapter is completed.

---

### Dependencies

| Dependency | Type | Owner | Status |
|------------|------|-------|--------|
| INIT-LAH-001 | Blocker | Chris Kreager | Draft |

---

### Out of Scope

- Full adapter implementations
- Memory orchestration beyond what is required to shape core contracts

---

### Artifacts

- [ ] Figma / Jira Comps: N/A
- [x] Workflow Diagram: [local_llm_agent_harness_modern_stacks.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/local_llm_agent_harness_modern_stacks.md)
- [ ] [Other artifacts]

---

### I Know I Am Done When

- [ ] Story-level contracts are approved.
- [ ] Ledger and compiler behavior are described clearly enough to drive downstream implementation.
- [ ] The epic’s outputs are testable through later adapter and workflow stories.

---

### User Stories

| Order | # | Story Title | Description | Points | Hours | Dependencies | QA Can Test |
|-------|---|-------------|-------------|--------|-------|--------------|-------------|
| 1 | US-LAH-001 | Define canonical runtime contracts and run profiles | Define the shared internal model for events, run profiles, and turn results. | 5 | 20 | None | Yes |
| 2 | US-LAH-002 | Implement append-only session ledger and context compiler | Turn the runtime model into ledger and compiler behavior. | 8 | 36 | US-LAH-001 | Yes |
| | | | **Total** | **13** | **56** | | |

**Sequence & Sizing Rationale:**
- Development efficiency: contracts first, compiler and ledger second.
- Risk reduction: interface uncertainty is retired before implementation spreads.
- Value delivery: even partial completion gives the team a shared planning and design language.

---

### Questions for Tech Lead

- Which contract fields must remain stable across all adapters?
- What visibility metadata belongs in the ledger from day one?

---

## ⚙️ TECH LEAD SECTION

### Impacted Functional Areas

| Functional Area | Impact Level | Primary Files | Notes |
|-----------------|--------------|---------------|-------|
| Durable state | High | `broker/durable_state.py` | Ledger model and compaction behavior |
| Prompting | High | `broker/prompting.py` | Compiler behavior and model-facing assembly |
| Session store | Medium | `broker/session_store.py` | Runtime state model |

---

### High-Level Technical Notes

- The compiler should consume canonical events and emit provider-specific requests.
- Ledger fidelity and model-facing context shaping must remain separate concerns.

---

### Code Areas to Examine

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Prompt assembly | `broker/prompting.py` | Context compilation |
| Module | Durable state | `broker/durable_state.py` | Event sourcing and compaction |
| Module | Session runtime | `broker/session_store.py` | Session state representation |

---

### Database Considerations

| Change Type | Object | Migration Script Needed |
|-------------|--------|------------------------|
| Data Model | Session ledger representation | No |

---

### Shared Components

- Canonical runtime contracts: Used in Stories US-LAH-001 and US-LAH-002

---

### Technical Dependencies

| System/API | What's Needed | Status |
|------------|---------------|--------|
| Existing broker runtime | Current session and trace behavior | Available |

---

### Cross-Area Impacts

| Area | Why It May Be Impacted | Mitigation |
|------|----------------------|------------|
| Tool broker | Contract definitions will influence future tool descriptors | Keep interfaces explicit and versionable |

---

### Potential Conflicts

- Ongoing broker prompt/reflection work could change the desired compiler seam.

---

### Performance Considerations

- Ledger compaction should preserve fidelity without making prompt assembly unbounded.

---

### Security/Compliance

- Visibility metadata must keep auth and operational data out of model-facing payloads by default.

---

### Regression Risk Areas

- [ ] Session recovery and compaction
- [ ] Prompt assembly behavior
- [ ] Trace fidelity

---

### Spike Needed?

- [x] Yes - Contract boundaries and visibility rules need validation before deeper implementation
- [ ] No

---

_Last Updated: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Technical Analysis By: Codex_
