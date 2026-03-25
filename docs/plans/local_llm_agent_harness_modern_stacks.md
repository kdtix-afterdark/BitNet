Modern stacks usually solve this with an **agent harness**, not by treating the raw chat transcript as the system boundary.

Codex’s public architecture shows a harness that runs an agent loop via the Responses API, builds the model input from structured fields like `instructions`, `tools`, and `input`, and orders roles with `system > developer > user > assistant`. The same Codex loop can point at local Responses-compatible endpoints, including local OSS backends. Claude’s low-level API exposes the same split in a different shape: you construct every turn, manage conversation state, and feed `tool_result` blocks back in response to `tool_use` blocks. GitHub Copilot adds another layer with persistent custom instructions, agent profiles, and MCP configuration. ([OpenAI][1])

MCP makes the reason even clearer. The protocol itself has **three** major surfaces—**tools**, **resources**, and **prompts**—but GitHub Copilot’s coding agent currently supports only MCP **tools**, not resources or prompts. So your internal model should not mirror any single provider’s message format. It should be a canonical runtime model that you later compile into OpenAI Responses, Anthropic Messages, or a local Llama-compatible prompt/tool format. ([Model Context Protocol][2])

A strong local-first architecture looks like this:

```text
UI / API
   |
   v
Session Ledger  <---->  Artifact Store
   |
   v
Context Compiler
   |
   v
Agent Runtime / Turn Engine
   |        |         |          |           |
   |        |         |          |           |
   v        v         v          v           v
Model   Tool Broker  Memory   Workflow   Policy/Approval
Router   + MCP        Layer    Engine      + Sandbox
   |
   v
Tracing / Evals / Audit
```

### 1) Make the session ledger the source of truth

Do not store “the prompt” as your primary state. Store an append-only ledger of events:

* policy/system instructions
* agent profile / developer instructions
* user messages
* assistant messages
* tool calls
* tool results
* memory reads/writes
* summaries / compactions
* approvals / denials
* artifacts
* ops metadata such as `requestType`, `traceId`, budget, tenant, auth scope

The important twist is to add **visibility** to each record: `visible_to_model`, `visible_to_user`, `visible_to_ops`. That prevents `requestType`, auth data, retry counts, raw headers, and trace IDs from leaking into the model unless they truly matter. This matches the way mature stacks separate conversation history, approvals, and streamed runtime events from the model-facing payload. ([OpenAI Developers][3])

### 2) Build a context compiler, not a transcript formatter

Your compiler should take:

* current session events
* `requestType`
* model/provider capability profile
* active tools / MCP servers
* budget / max turns / sandbox policy
* selected memory hits

and emit a provider-specific request.

That compiler is where `requestType` should usually live. In other words, `requestType` should mostly select a **run profile**:

* model family
* reasoning effort
* allowed tools / MCP servers
* max turns
* sandbox/network profile
* memory namespaces
* output schema

Only inject a short developer instruction when the mode changes the task identity, such as “act as a code-fixing agent” versus “act as a research agent.” This is much closer to how Codex layers instructions and configs, and how Copilot layers personal, repository, and organization instructions. ([OpenAI][1])

### 3) Treat provider adapters as capability translators

You want one internal interface such as:

```ts
runTurn(sessionState, runProfile, toolCatalog) -> TurnResult
```

Then write adapters.

**Responses-style adapter.** OpenAI Responses is already built around structured inputs, tools, and stateful conversations, and Codex uses it as the core agent-loop transport. That makes it a very good target shape for your internal runtime. ([OpenAI Platform][4])

**Anthropic adapter.** Claude’s Messages API uses `tool_use` and `tool_result` blocks. If you use extended thinking, Anthropic’s docs are explicit that the corresponding thinking block must be returned unmodified during that tool cycle, then can be dropped afterward. That is a strong signal that provider-specific “thinking” should be treated as a transport artifact, not your durable memory format. Persist your own explicit planning objects instead. ([Claude][5])

**Local/open-weight adapter.** For Llama or other local models, the cleanest move is to expose an OpenAI-compatible Chat endpoint and, if you can, a Responses-compatible endpoint. Codex can already target local Responses-compatible servers, while the OpenAI Agents SDK notes that many providers still do not support Responses and may require a chat-completions fallback. Llama Stack’s own framing—unified APIs for inference, RAG, agents, tools, and safety with provider flexibility—fits this adapter-first design well. ([OpenAI][1])

For this team’s actual workflow, the implementation order should be:

1. Responses-compatible adapter first
2. MCP broker and lowering path second, because GitHub Copilot Chat and Warp are the highest-frequency daily surfaces
3. Anthropic Messages adapter third to prove portability across a different transport
4. Native local fallback adapter last, and only if a required local backend cannot remain behind a Responses-compatible surface

### 4) Normalize all tools behind one tool broker

Your broker should expose a canonical `ToolDescriptor`:

```ts
{
  name,
  description,
  input_schema,
  output_schema,
  side_effects: "read_only" | "mutating",
  auth_scope,
  timeout_ms,
  requires_approval,
  backend: "native" | "local_fn" | "mcp",
  server_ref?
}
```

That shape works well because OpenAI tools, Anthropic tools, and MCP tools are all schema-driven. Anthropic even documents direct conversion from MCP `inputSchema` to Claude `input_schema`. ([OpenAI Platform][6])

Inside the broker, support three classes:

**Native provider tools.** Use native web search, file search, code tools, or computer tools when the provider offers them. That gives you less glue code and better model/tool alignment. OpenAI exposes built-in tools in Responses, and Claude’s SDK exposes built-in tools plus MCP. ([OpenAI Platform][4])

**Local general tools.** Wrap your own file search, SQL, shell, retrieval, or business logic as local functions.

**MCP.** Support local STDIO servers and remote HTTP servers. MCP servers can expose tools, resources, and prompts, but your adapter may need to lower resources/prompts into plain context for clients that only understand tools. GitHub’s coding agent limitation proves why this lowering layer matters. Anthropic and OpenAI both expose allowlists/read-only filters around MCP access, and Anthropic explicitly warns that remote MCP servers are third-party systems you should trust only deliberately. ([GitHub Docs][7])

### 5) Split memory into hot, warm, and cold layers

A durable pattern is:

* **hot context**: current turn and immediate working set
* **warm episodic memory**: summaries, checkpoints, decisions, partial conclusions
* **cold semantic memory**: facts, embeddings, documents, artifacts

Do not use one giant rolling transcript. Use compaction and checkpoint summaries as first-class events. Anthropic’s tool runner supports automatic compaction, its memory tool is explicitly for storing/retrieving information across conversations, and its context-editing docs describe preserving important information to memory before older tool results are cleared. OpenAI’s Codex stack likewise uses compaction to keep long-running tasks going near context limits. ([Claude][8])

A practical rule: persist **facts, decisions, summaries, evidence, and artifacts**. Do not persist raw hidden reasoning as your memory layer.

### 6) Model “Sequential Thinking” as explicit planner state

Do not rely on hidden chain-of-thought as your architecture.

Represent planning explicitly, for example:

```json
{
  "goal": "...",
  "assumptions": ["..."],
  "evidence": ["artifact:123", "tool_result:456"],
  "next_actions": ["search docs", "read file x", "run tests"],
  "open_questions": ["..."],
  "done_criteria": ["tests pass", "schema validated"]
}
```

This gives you a provider-neutral planning state you can summarize, diff, checkpoint, and audit. It also avoids coupling your system to provider-specific thinking semantics, which Anthropic’s tool-cycle rules make especially brittle. ([Claude][9])

### 7) Separate the **turn loop** from the **workflow loop**

Use two loops.

The **turn loop** is the local plan/act/observe cycle: model proposes tool calls, tools run, results go back, repeat until no more tool calls.

The **workflow loop** is the durable job runner around it: retries, timeouts, approvals, fan-out, checkpoints, resumptions, SLA handling, and subagent orchestration.

Claude documents a turn exactly this way. OpenAI’s Agents SDK distinguishes code-driven orchestration from LLM-driven orchestration, and handoffs are represented as tools. Anthropic subagents are explicitly for isolating context, running focused subtasks, and parallelizing work. That leads to a good default design: keep the workflow graph code-driven where determinism matters, and let the model choose tools or specialists only inside bounded regions. ([Claude][10])

### 8) Treat specialists as tools or handoffs, not as free-floating agents

The cleanest multi-agent pattern is:

* one router/manager agent
* a few specialist agents
* each specialist exposed as either a tool or a handoff target
* narrow toolsets per specialist
* narrow memory namespaces per specialist

That maps directly to OpenAI’s handoff model and Anthropic’s subagent model. It also keeps prompt bloat under control. Be careful with permissions inheritance: Anthropic notes that permissive modes can propagate to subagents, and subagents may have different prompts and looser behavior. ([OpenAI GitHub][11])

### 9) Put policy, approvals, and sandboxing at the broker boundary

This is one of the biggest differences between toy agents and production agents.

Use a default of:

* read-only tools auto-approved
* mutating tools require approval or privileged run profile
* network off by default
* write access scoped to workspace
* secrets kept outside the agent boundary

Codex documents a secure sandbox-by-default posture, with file writes limited to the workspace and network disabled unless enabled. Anthropic’s secure deployment guidance recommends the same core ideas: isolation, least privilege, defense in depth, and a proxy pattern that injects credentials outside the agent’s boundary. It also explicitly recommends routing authenticated access through MCP/custom tools or proxies so the agent never sees the raw credentials. ([OpenAI][12])

For MCP specifically, use tool metadata and policy together. MCP has `readOnlyHint`, and both OpenAI and Anthropic expose allowlist / approval controls around tools. That makes “read-only first, escalate later” a natural policy model. ([Model Context Protocol][13])

### 10) Make tracing and evals first-class from day one

Do not bolt observability on later. Every run should emit spans for:

* model call
* tool call
* tool result size
* memory retrieval
* memory write
* approval wait
* handoff/subagent
* compaction
* final artifact generation

OpenAI’s Agents SDK has built-in tracing for LLM generations, tool calls, handoffs, guardrails, and custom events, and Codex’s app-server is explicitly built around conversation history, approvals, and streamed agent events. That is the right mental model for your own broker as well. ([OpenAI GitHub][14])

## The design pattern I’d use for your stack

In one line:

**append-only session ledger → context compiler → capability-aware model router → unified tool/MCP broker → hot/warm/cold memory → durable workflow engine → approval/sandbox boundary → tracing/evals**

That gives you a system that can speak to local Llama-class models, OpenAI-style Responses backends, and Anthropic-style Messages backends without rewriting your entire runtime every time a provider changes its surface.

The next useful step is to define four internal contracts before writing more code: `Event`, `RunProfile`, `ToolDescriptor`, and `TurnResult`.

One operational constraint matters for rollout planning: true BitNet UAT still requires the local Apple Silicon plus Metal execution path. GitHub-hosted or cloud environments can help with planning, review, and limited CPU verification, but they should not be treated as equivalent to authoritative local BitNet validation.

[1]: https://openai.com/index/unrolling-the-codex-agent-loop/ "https://openai.com/index/unrolling-the-codex-agent-loop/"
[2]: https://modelcontextprotocol.io/specification/2025-11-25/server/tools "https://modelcontextprotocol.io/specification/2025-11-25/server/tools"
[3]: https://developers.openai.com/codex/app-server/ "https://developers.openai.com/codex/app-server/"
[4]: https://platform.openai.com/docs/api-reference/responses/list?ref=test-ippon.ghost.io "https://platform.openai.com/docs/api-reference/responses/list?ref=test-ippon.ghost.io"
[5]: https://platform.claude.com/docs/en/claude_api_primer "https://platform.claude.com/docs/en/claude_api_primer"
[6]: https://platform.openai.com/docs/api-reference/realtime-server-events/input_audio_buffer?_clear=true&lang=node.js&utm_source=chatgpt.com "https://platform.openai.com/docs/api-reference/realtime-server-events/input_audio_buffer?_clear=true&lang=node.js&utm_source=chatgpt.com"
[7]: https://docs.github.com/en/copilot/concepts/agents/coding-agent/mcp-and-coding-agent "https://docs.github.com/en/copilot/concepts/agents/coding-agent/mcp-and-coding-agent"
[8]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use"

## Execution Plan

The planning hierarchy for this modernization effort has now been generated as an issue-ready set under [docs/plans/artifacts/local_llm_agent_harness_modern_stacks/README.md](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/README.md). Those files are structured for later creation in [GitHub Project 2](https://github.com/orgs/kdtix-afterdark/projects/2) and already include:

- issue type
- labels
- parent relationships
- `Blocks` / `Blocked By` dependency metadata

### GitHub Project Mapping

- Project: `BitNet Enhancements`
- Repository: `kdtix-afterdark/BitNet`
- Status field: `Backlog`, `Ready`, `In progress`, `In review`, `Done`
- Size field: `XS`, `S`, `M`, `L`, `XL`
- Priority field: `P0`, `P1`, `P2`
- Parent field: `Parent issue`

### Relationship Model

- Project Scope < Initiative < Epic < Story < Task
- Project Scope defines the modernization outcome and overall delivery guardrails.
- Initiative groups the runtime foundation work into four delivery epics.
- Epics organize the work into runtime core, adapter/tooling, memory/workflow, and readiness slices.
- Stories are the first implementation-shaped units.
- Tasks break stories into 1-4 hour engineering steps aligned to the supplied templates.

### Planning Index

- Project Scope: [PS-LAH-001 Local LLM Agent Harness Modernization](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/PS-LAH-001_project_scope.md)
- Initiative: [INIT-LAH-001 Provider-Neutral Local Agent Harness Foundation](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/INIT-LAH-001_initiative.md)

### Epic Breakdown

| Order | Epic | Focus | Blocked By | Stories |
|---|---|---|---|---|
| 1 | [EP-LAH-001 Runtime Core and Context Compiler](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-001_runtime_core_context_compiler.md) | Canonical contracts, session ledger, context compiler | Initiative | US-LAH-001, US-LAH-002 |
| 2 | [EP-LAH-002 Provider Adapters and Tool Broker](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-002_provider_adapters_and_tool_broker.md) | Provider adapters, tool normalization, MCP lowering | EP-LAH-001 | US-LAH-003, US-LAH-004 |
| 3 | [EP-LAH-003 Memory Workflow and Policy Controls](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-003_memory_workflow_and_policy_controls.md) | Hot/warm/cold memory, planner state, workflow and approvals | EP-LAH-001, EP-LAH-002 | US-LAH-005, US-LAH-006 |
| 4 | [EP-LAH-004 Observability and Modern Stack Readiness](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/EP-LAH-004_observability_and_modern_stack_readiness.md) | Tracing, evals, VS Code integration, docs, UAT, rollout readiness | EP-LAH-001, EP-LAH-002, EP-LAH-003 | US-LAH-007, US-LAH-009, US-LAH-008 |

### Story Breakdown

| Story | Parent Epic | Focus | Blocked By | Task Count |
|---|---|---|---|---|
| [US-LAH-001 Define canonical runtime contracts and run profiles](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-001_canonical_runtime_contracts_and_run_profiles.md) | EP-LAH-001 | Canonical `Event`, `RunProfile`, `ToolDescriptor`, `TurnResult` | None | 2 |
| [US-LAH-002 Implement append-only session ledger and context compiler](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-002_session_ledger_and_context_compiler.md) | EP-LAH-001 | Ledger, visibility rules, context compilation | US-LAH-001 | 2 |
| [US-LAH-003 Implement provider adapter layer with Responses-compatible first delivery](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-003_provider_adapter_layer.md) | EP-LAH-002 | Responses-compatible adapter foundation, with Anthropic and native fallback sequenced later | US-LAH-001 | 2 |
| [US-LAH-004 Normalize tool broker and MCP translation for Copilot-first workflows](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-004_tool_broker_and_mcp_translation.md) | EP-LAH-002 | Unified broker, tool descriptors, MCP lowering for Copilot Chat and Warp usage | US-LAH-003 | 2 |
| [US-LAH-005 Implement hot warm cold memory and planner state](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-005_memory_layers_and_planner_state.md) | EP-LAH-003 | Memory layers, retention, planner state | US-LAH-002, US-LAH-004 | 2 |
| [US-LAH-006 Separate workflow orchestration from turn execution and approvals](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-006_workflow_orchestration_and_approvals.md) | EP-LAH-003 | Workflow loop, approval gates, specialist routing | US-LAH-005 | 2 |
| [US-LAH-007 Emit tracing eval and audit spans](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-007_tracing_evals_and_audit_spans.md) | EP-LAH-004 | Tracing, evals, audit artifacts | US-LAH-002, US-LAH-004, US-LAH-006 | 2 |
| [US-LAH-009 Enable productized VS Code Chat integration through a Responses-compatible BitNet provider](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-009_vscode_chat_integration_via_responses_provider.md) | EP-LAH-004 | Supported VS Code model-provider path for long-term UAT and daily local use | US-LAH-003, US-LAH-004, US-LAH-007 | 2 |
| [US-LAH-008 Deliver readiness docs and UAT for modern stacks](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-008_modern_stack_readiness_and_uat.md) | EP-LAH-004 | Docs, run profiles, UAT, rollout checklist including VS Code validation | US-LAH-003, US-LAH-004, US-LAH-006, US-LAH-007, US-LAH-009 | 2 |

### Task Set

The story-level breakdown has been expanded into twenty template-based tasks:

1. [TASK-LAH-001 Event TurnResult and Visibility Contracts](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-001_event_turnresult_and_visibility_contracts.md)
2. [TASK-LAH-002 Run Profile and Capability Matrix](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-002_run_profile_and_capability_matrix.md)
3. [TASK-LAH-003 Session Ledger Event Model and Visibility Rules](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-003_session_ledger_event_model_and_visibility_rules.md)
4. [TASK-LAH-004 Context Compiler Assembly and Regression Coverage](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md)
5. [TASK-LAH-005 Adapter Interface and Capability Translator](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-005_adapter_interface_and_capability_translator.md)
6. [TASK-LAH-006 Responses Anthropic and Local Adapter Implementation](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-006_responses_anthropic_and_local_adapter_implementation.md)
7. [TASK-LAH-007 Tool Descriptor and Policy Contract](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-007_tool_descriptor_and_policy_contract.md)
8. [TASK-LAH-008 MCP Lowering and Broker Registration](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-008_mcp_lowering_and_broker_registration.md)
9. [TASK-LAH-009 Memory Layer Contract and Retention Rules](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-009_memory_layer_contract_and_retention_rules.md)
10. [TASK-LAH-010 Planner State Checkpointing and Memory Selection](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-010_planner_state_checkpointing_and_memory_selection.md)
11. [TASK-LAH-011 Workflow Engine Separation and Job Semantics](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-011_workflow_engine_separation_and_job_semantics.md)
12. [TASK-LAH-012 Approval Sandbox and Specialist Routing](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-012_approval_sandbox_and_specialist_routing.md)
13. [TASK-LAH-013 Trace Taxonomy and Span Emission](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-013_trace_taxonomy_and_span_emission.md)
14. [TASK-LAH-014 Eval Hooks and Audit Artifact Capture](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-014_eval_hooks_and_audit_artifact_capture.md)
15. [TASK-LAH-015 Modern Stack Docs and Run Profiles](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-015_modern_stack_docs_and_run_profiles.md)
16. [TASK-LAH-016 End-to-End UAT and Readiness Checklist](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-016_end_to_end_uat_and_readiness_checklist.md)
17. [TASK-LAH-017 Responses Endpoint and VS Code Integration Contract](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-017_responses_endpoint_and_vscode_integration_contract.md)
18. [TASK-LAH-018 VS Code Model Provider Extension and UAT Path](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-018_vscode_model_provider_extension_and_uat_path.md)
19. [TASK-LAH-019 Port Plain-Chat Prompting](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-019_port_plain_chat_prompting.md)
20. [TASK-LAH-020 Clean-Lab Apple Silicon Bootstrap and GGUF Dependency Spike](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-020_clean_lab_bootstrap_and_gguf_dependency_spike.md)

### Delivery Summary

- 1 project scope
- 1 initiative
- 4 epics
- 9 stories
- 20 tasks

This plan is now populated both at the architecture level in this document and at the issue-ready level in the linked planning set.
[9]: https://platform.claude.com/docs/en/build-with-claude/context-windows "https://platform.claude.com/docs/en/build-with-claude/context-windows"
[10]: https://platform.claude.com/docs/en/agent-sdk/agent-loop "https://platform.claude.com/docs/en/agent-sdk/agent-loop"
[11]: https://openai.github.io/openai-agents-python/handoffs/ "https://openai.github.io/openai-agents-python/handoffs/"
[12]: https://openai.com/index/gpt-5-1-codex-max/ "https://openai.com/index/gpt-5-1-codex-max/"
[13]: https://modelcontextprotocol.io/specification/draft/schema "https://modelcontextprotocol.io/specification/draft/schema"
[14]: https://openai.github.io/openai-agents-python/tracing/ "https://openai.github.io/openai-agents-python/tracing/"
