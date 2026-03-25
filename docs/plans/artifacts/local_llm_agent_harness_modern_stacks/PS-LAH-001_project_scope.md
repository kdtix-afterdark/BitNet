# Project Scope: PS-LAH-001 Local LLM Agent Harness Modernization

> **Issue Type**: Project Scope
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Repository**: `kdtix-afterdark/BitNet`
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `local-llm`
> **Blocks**: INIT-LAH-001
> **Blocked By**: None

---

> **Status**: Draft
> **Target Timeframe**: TBD
> **Project Scope Owner**: Chris Kreager

---

## Vision

Deliver a provider-neutral local agent harness that can orchestrate models, tools, MCP, memory, workflow control, and observability across modern stacks without coupling the product to any single chat transcript format.

---

## Business Problem & Current State

Today, local agent implementations tend to treat the raw chat transcript as the system boundary. That makes provider changes expensive, weakens policy separation, mixes audit state with model state, and makes it harder to support OpenAI-style Responses, Anthropic-style Messages, and local OSS backends from one runtime. The result is slower iteration, brittle integrations, and higher operational risk for teams trying to ship local-first coding and agent experiences.

---

## Success Criteria

- [ ] The team has one canonical runtime model that can target at least one hosted provider shape and one local OSS backend shape without redesigning the harness.
- [ ] Session state, memory, workflow, and approvals are separated cleanly enough to support auditability and restart-safe execution.
- [ ] The harness has enough tracing, evaluation, and UAT coverage to validate local-first agent runs on modern stacks before broader rollout.

---

## In-Scope Capabilities

**Provider-neutral local agent harness foundation** [INIT-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/INIT-LAH-001_initiative.md)
- Canonical ledger, context compilation, and run-profile model
- Provider adapters, unified tool broker, MCP lowering, memory, workflow, policy, tracing, and readiness validation

---

## Assumptions

- The first release should optimize for local-first execution and adapter flexibility, not for every provider-specific advanced feature on day one.
- GitHub Project 2 will be used as the work management surface for the resulting Initiative, Epics, Stories, and Tasks.

---

## Out of Scope

- Building every possible provider adapter in the first release
- Full productization of UI surfaces beyond what is needed to validate the harness architecture

---

## I Know I Am Done When

- [ ] One approved Initiative exists with a complete Epic, Story, and Task hierarchy for this scope.
- [ ] The planned hierarchy covers runtime model, tools/MCP, memory/workflow/policy, and observability/readiness.
- [ ] Dependencies and sequencing are clear enough for backlog ordering and incremental delivery.
- [ ] The planning set can be copied into GitHub Project 2 without structural rework.

---

## Initiatives

| # | Initiative | Description | Status |
|---|------------|-------------|--------|
| 1 | [INIT-LAH-001](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/INIT-LAH-001_initiative.md) | Build the provider-neutral local agent harness foundation and the delivery plan around it. | Draft |

---

_Created: 2026-03-21_
_Owner: Chris Kreager_
