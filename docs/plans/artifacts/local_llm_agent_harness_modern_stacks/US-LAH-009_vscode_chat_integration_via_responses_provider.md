# User Story: US-LAH-009 Enable productized VS Code Chat integration through a Responses-compatible BitNet provider

> **Issue Type**: Story
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `vscode`, `lm-provider`, `responses`, `integration`
> **Blocks**: US-LAH-008
> **Blocked By**: US-LAH-003, US-LAH-004, US-LAH-007

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

```text
As a developer using BitNet locally in VS Code,
I want a productized VS Code Chat integration that talks to a Responses/OpenAI-compatible BitNet endpoint,
So that I can perform repeatable UAT and daily local-model work inside VS Code without relying on a bespoke broker-only chat contract.
```

---

### TL;DR

Create a long-term VS Code model-provider path for BitNet that uses a standardized Responses/OpenAI-compatible broker surface and becomes a supported UAT environment.

---

### Why This Matters

The draft GitHub item is directionally useful, but it currently assumes a direct dependency on the broker’s bespoke `/chat` contract. That would create another client-specific seam. This story aligns the VS Code integration with the broader harness plan by making VS Code consume the same standardized adapter surface we want long term, while also giving the team a realistic daily UAT environment.

---

### Assumptions

- **Roles**: Developer, platform engineer, tester
- **Starting point**: Responses-compatible adapter direction is agreed
- **Preconditions**: Adapter, MCP/tool broker, and tracing foundations exist
- **Environment constraint**: Real BitNet UAT for this story happens on the user’s local Metal-capable setup; GitHub-hosted or cloud environments may validate the integration path only in CPU-limited form

---

### Dependencies

| Ticket | Description | Status |
|--------|-------------|--------|
| [US-LAH-003](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-003_provider_adapter_layer.md) | Responses-compatible adapter foundation | Blocked |
| [US-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-004_tool_broker_and_mcp_translation.md) | MCP/tool broker readiness | Blocked |
| [US-LAH-007](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-007_tracing_evals_and_audit_spans.md) | Trace-backed UAT evidence | Blocked |

---

### I Know I Am Done When

- [ ] The broker exposes a stable Responses/OpenAI-compatible endpoint intended for VS Code consumption.
- [ ] The VS Code integration uses the supported model-provider path instead of the bespoke `/chat` contract.
- [ ] A tester can execute a repeatable VS Code Chat UAT scenario and correlate it to broker traces and session state.
- [ ] Productization concerns such as settings, reachability checks, error handling, and setup docs are captured.

---

### Acceptance Criteria

**Scenario 1**: Standardized endpoint
- **Given**: the BitNet broker is running locally
- **When**: the VS Code integration sends a chat turn
- **Then**: it uses a Responses/OpenAI-compatible endpoint rather than a one-off `/chat` contract

**Scenario 2**: VS Code model-provider integration
- **Given**: the VS Code integration is installed and configured
- **When**: the user opens VS Code Chat and selects a model
- **Then**: BitNet appears through the supported model-provider path and can be used without leaving VS Code

**Scenario 3**: Trace-backed UAT
- **Given**: a tester runs a scripted or manual UAT scenario in VS Code on the local Metal-backed BitNet setup
- **When**: they inspect the resulting evidence
- **Then**: they can correlate the VS Code session to broker traces, session state, and readiness artifacts

**Scenario 4**: Long-term supportability
- **Given**: the broker is down, misconfigured, or not reachable
- **When**: the user tries to use BitNet in VS Code
- **Then**: the integration reports a clear, actionable error and the setup path remains supportable

---

### Constraints

- Do not depend on modifying any GitHub-controlled model picker backend
- Do not introduce another bespoke client contract if a standardized endpoint can be used
- Keep the integration supportable as a long-term product surface, not just a throwaway UAT shim
- Do not treat GitHub-hosted or generic cloud execution as equivalent to the local Metal-backed BitNet validation path

---

### Questions for Engineering

- Which VS Code version range and model-provider path are in scope for the first supported release?
- What minimum streaming and correlation behavior is required for credible VS Code UAT?
- Which CPU-only checks are still worth running in GitHub or the cloud without overstating parity with local BitNet behavior?

---

## ⚙️ ENGINEERING SECTION

### Implementation Options

| Option | Approach | LOE | Trade-offs |
|--------|----------|-----|------------|
| A | Thin VS Code extension against existing `/chat` | 5 pts / 16-24 hrs | Fastest start. Creates another custom client seam. |
| B | Productized VS Code model provider against Responses/OpenAI-compatible endpoint | 5 pts / 16-24 hrs | Best long-term fit. Requires standardizing the broker surface first. |
| C | Use only manual OpenAI-compatible configuration with no owned integration | 5 pts / 16-24 hrs | Lowest maintenance. Weak long-term product control and weaker UAT packaging. |

**Recommended**: B because it aligns the VS Code experience to the same standardized endpoint strategy the harness needs long term.

---

### Subtasks

| Area | Needed | Subtask | Est. Hours |
|------|--------|---------|------------|
| ⚙️ Backend | Y | [TASK-LAH-017](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-017_responses_endpoint_and_vscode_integration_contract.md) | 4 |
| 🖥️ UI | Y | [TASK-LAH-018](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-018_vscode_model_provider_extension_and_uat_path.md) | 4 |
| 🧪 Test/Verify | Y | Validate VS Code Chat selection, broker reachability, and trace correlation | 3 |

---

### Code Areas

| Type | Object | Location | Notes |
|------|--------|----------|-------|
| Module | Broker API surface | `broker/server.py`, `broker/llama_runtime.py` | Responses/OpenAI-compatible integration seam |
| Folder | VS Code integration | `vscode-bitnet-provider/` | Long-term model-provider extension candidate |
| Script | UAT tooling | `run_conversation_uat.py`, `monitor_broker_debug.py` | Evidence correlation |

---

### Regression Risk

- [ ] Endpoint compatibility drift between the broker and VS Code integration
- [ ] VS Code API/version assumptions aging out
- [ ] Weak correlation between VS Code sessions and broker-side evidence

---

_Created: 2026-03-21_  
_Product Owner: Chris Kreager_  
_Tech Lead: TBD._
