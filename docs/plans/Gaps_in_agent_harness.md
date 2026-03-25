# Gaps in the Agent Harness Sequence Diagram

## Gap Analysis: Sequence Diagram ↔ Planning Doc ↔ Artifacts

### A. Gaps in the Sequence Diagram (concepts well-covered in the planning doc/artifacts but missing or underspecified in the `.mmd`)

---

#### 1. Policy / Sandbox Boundary Is Not a Participant

The planning doc (§9) makes policy, approvals, and sandboxing a first-class architectural boundary — "read-only auto-approved, mutating requires approval, network off by default, write access scoped to workspace." The diagram's `opt approval gate` only models the human-in-the-loop approve/deny flow via the UI. There is no participant or gate representing the **automated policy engine** that would auto-approve read-only tools, enforce sandbox constraints, or scope network/write access.

| | |
|---|---|
| **Pro of adding it** | Matches the planning doc's §9 contract and TASK-LAH-012 (approval, sandbox, specialist routing). Clarifies that most tool calls never reach the user — they are policy-decided. Prevents implementers from assuming approval always means human roundtrip. |
| **Con of adding it** | Adds a participant to an already dense diagram. Policy/sandbox could be modeled as internal logic within `WF` or `TB` rather than a distinct swimlane. |
| **Recommendation** | Add a `Policy Gate` participant between `WF` and `TB`, or at minimum add a `break` / `alt` before `WF->>TB: execute act` showing the policy check path (auto-approve vs escalate to UI). |

---

#### 2. Provider Adapter Layer Is Invisible

The planning doc (§3) and artifacts (US-LAH-003, TASK-LAH-005, TASK-LAH-006) define a capability-translating adapter layer between the runtime and model providers. The diagram's `MR` (Model Router / LLM) receives `infer(context, tool catalog)` and returns a decision, but there's no indication that `MR` internally selects a provider and translates the canonical request into Responses / Anthropic Messages / local Llama format.

| | |
|---|---|
| **Pro of adding it** | Makes the multi-provider story visible — the core architectural differentiator of this harness. Prevents treating Model Router as a monolithic black box. |
| **Con of adding it** | The adapter is an internal implementation detail of `MR`. Exposing it as a separate participant may over-complicate the diagram for audiences who don't need to see transport details. |
| **Recommendation** | Keep `MR` as one participant but add a note (`Note over MR: Selects adapter per RunProfile<br/>(Responses, Anthropic, Local)`). |

---

#### 3. Run Profile / `requestType` Selection Is Missing

The planning doc (§2) and artifacts (TASK-LAH-002) define RunProfile as the mechanism that maps a `requestType` to model family, reasoning effort, allowed tools, max turns, sandbox policy, memory namespaces, and output schema. The diagram's `UI->>WF: start run` carries no profile context, and the `CC: build context` step doesn't show RunProfile as an input.

| | |
|---|---|
| **Pro of adding it** | RunProfile is the central control surface for the entire run. Without it, the diagram implies every run is identical. |
| **Con of adding it** | Minor addition — just parameter decoration on existing arrows. |
| **Recommendation** | Change `UI->>WF: start run` to `UI->>WF: start run(run_profile)` and `WF->>CC: build context(run_profile)`. |

---

#### 4. Turn Loop vs Workflow Loop Conflation

The planning doc (§7) and artifacts (US-LAH-006, TASK-LAH-011) explicitly separate the **turn loop** (infer → tool → observe, repeat until no more tool calls) from the **workflow loop** (retries, timeouts, approvals, fan-out, checkpoints, resumptions). The diagram merges both into a single `alt` block under `WF`. The `WF->>MR: next inference` at the end of the block suggests one more cycle, but the iterative nature of the turn loop (potentially many infer→tool→observe cycles) is not shown.

| | |
|---|---|
| **Pro of adding it** | This is called out as one of the biggest architectural distinctions in §7. Implementers need to know that the turn loop repeats autonomously while the workflow loop controls job-level behavior. |
| **Con of adding it** | Mermaid sequence diagrams model loops awkwardly. Adding a `loop` block inside the `alt` would make the diagram significantly more complex. |
| **Recommendation** | Add a `loop turn_loop (until no tool calls or budget exhausted)` block wrapping the infer→tool→observe→rebuild cycle within the existing `alt`. Add a note clarifying the workflow loop is the outer frame. |

---

#### 5. Specialist / Handoff / Subagent Routing

The planning doc (§8) and artifacts (TASK-LAH-012) describe specialists as bounded tools or handoff targets with narrow toolsets and memory namespaces. The diagram's `Note over WF,SL` mentions "handoff" as an act type, but there is no flow showing how a handoff actually works — spawning a subagent, isolating its context, returning its result.

| | |
|---|---|
| **Pro of adding it** | Multi-agent routing is a first-class design pattern in the planning doc. Without it, the diagram cannot guide implementation of TASK-LAH-012. |
| **Con of adding it** | Specialists are essentially recursive invocations of the same flow with narrower scope. Modeling a full subagent sequence inside the parent diagram would double its length. |
| **Recommendation** | Add a single `opt handoff to specialist` block showing `WF->>WF: spawn(specialist_profile, scoped_tools, scoped_memory)` with a return, and reference a separate specialist sequence diagram for the full flow. |

---

#### 6. Explicit Planner State Object

The planning doc (§6) and artifacts (TASK-LAH-010) define explicit planner state — `goal`, `assumptions`, `evidence`, `next_actions`, `open_questions`, `done_criteria` — as a checkpoint-able, auditable, diff-able object. The diagram's `decision_record` appended to SL could implicitly contain this, but the planner state lifecycle (create, update, checkpoint, resume) is not shown.

| | |
|---|---|
| **Pro of adding it** | Planner state is the explicit alternative to hidden CoT. Making it visible in the diagram reinforces the architectural decision from §6. |
| **Con of adding it** | It could be treated as payload content within the existing `decision_record` and `summary_checkpoint` events. |
| **Recommendation** | Add a `WF->>SL: append(planner_state_update)` step after each `MR-->>WF: decision`, or add a note clarifying that `decision_record` includes the structured planner state. |

---

#### 7. Visibility Rules on Ledger Events

The planning doc (§1) and artifacts (TASK-LAH-001, TASK-LAH-003) emphasize that every ledger event carries `visible_to_model`, `visible_to_user`, `visible_to_ops` metadata. The diagram shows `CC->>SL: read recent events` but doesn't indicate that the Context Compiler **filters by visibility**. Likewise, `WF->>SL: append(...)` calls don't show visibility assignment.

| | |
|---|---|
| **Pro of adding it** | Visibility is the mechanism preventing ops metadata, trace IDs, and auth data from leaking into model context. It's called out as "the important twist" in §1. |
| **Con of adding it** | Notes on every `append()` call would create visual noise. |
| **Recommendation** | Add a single note on the first `append()` call: `Note over SL: All events carry visibility<br/>(model / user / ops)`, and annotate `CC->>SL: read recent events` as `CC->>SL: read events(visible_to_model)`. |

---

#### 8. Compaction as a Distinct Operation

The planning doc (§5) describes compaction and checkpoint summaries as first-class events. The diagram has `opt checkpoint hit` with memory writes, but **compaction** — the eviction of old events from hot context and replacement with summaries — is not shown. The `CC: rebuild context with new refs` step implicitly benefits from compaction but the mechanics are absent.

| | |
|---|---|
| **Pro of adding it** | Compaction is the mechanism that prevents context window exhaustion in long-running tasks. It's essential for the hot/warm/cold memory layering in §5. |
| **Con of adding it** | Could be considered an implementation detail of the `checkpoint hit` block and the Context Compiler's internal logic. |
| **Recommendation** | Expand the `opt checkpoint hit` block to include `CC->>SL: compact(evict old events, retain summary_ref)` or add a note explaining that checkpoint includes compaction. |

---

#### 9. Error / Retry / Timeout Paths

The planning doc (§7) and artifacts (US-LAH-006, TASK-LAH-011) describe retries, timeouts, SLA handling, and resume behavior as workflow-loop responsibilities. The diagram is entirely happy-path — no tool failure, no model timeout, no retry, no budget exhaustion.

| | |
|---|---|
| **Pro of adding it** | Error handling defines the boundary between toy agents and production agents. Implementers need to know what happens when a tool fails or the model returns malformed output. |
| **Con of adding it** | Adding full error paths would at least double the diagram complexity. Sequence diagrams are poor at modeling retry loops and error branching. |
| **Recommendation** | Add a single `alt tool failure` block after `TB-->>WF: normalized result` showing `WF->>SL: append(act_failed)` → `WF->>CC: rebuild context` → retry or escalate. Keep it minimal — one block, not exhaustive paths. |

---

### B. Gaps in the Planning Doc / Artifacts (concepts the diagram models well but the doc/artifacts underspecify)

#### 1. Evidence Store Has No Dedicated Contract

The diagram gives Evidence Store first-class participant status with a clear contract: `persist(raw result, hash, provenance) → evidence_ref`. The planning doc mentions evidence in passing (§6 planner state, §10 tracing). The artifacts reference it under US-LAH-007/EP-LAH-004 but **no task explicitly defines the Evidence Store contract** — its immutability guarantees, hash algorithm, provenance schema, or retention policy.

**Recommendation**: Add a subtask under TASK-LAH-014 or create a new TASK-LAH-019 for the Evidence Store contract (schema, hash verification, provenance metadata, retention).

---

#### 2. Artifact Store Has No Dedicated Contract

Similarly, the diagram shows `AR: persist(versioned artifact blob + manifest) → artifact_ref` as a distinct participant. The artifacts mention "Artifact Store" implicitly in planner state and turn results, but **no task defines the artifact versioning scheme, manifest structure, or storage contract**.

**Recommendation**: Add a subtask under TASK-LAH-014 or create a new task for the Artifact Store contract (versioning, manifest schema, blob storage semantics, garbage collection).

---

#### 3. Act Lifecycle Granularity

The diagram shows a precise lifecycle: `act_intent → approval → act_started → act_finished(evidence_ref)`. This four-stage lifecycle for tool execution is not spelled out anywhere in the planning doc's prose or in the task descriptions. TASK-LAH-007 defines the `ToolDescriptor` and TASK-LAH-008 defines MCP lowering, but neither specifies the per-execution event lifecycle.

**Recommendation**: Document this lifecycle in TASK-LAH-003 (ledger event model) as a canonical event sequence for tool executions.

---

### C. Internal Consistency Within the Diagram

These are not gaps relative to the planning doc, but structural observations about the diagram itself:

| Issue | Detail |
|---|---|
| **No loop construct** | The `alt` block implies a single iteration. A `loop` around the infer→tool→observe cycle would be more accurate. |
| **`UI->>TR: start trace` ordering** | The trace starts at step 3, but `UI->>SL: append(user_message)` at step 2 happens before the trace. Should the first ledger event already be inside a trace span? |
| **`TB->>SL: append(act_started)` ownership** | The Tool Broker writes directly to the Session Ledger. In the planning doc's architecture, the Workflow Engine is the orchestrator — should `WF` write ledger events on behalf of `TB`, or is `TB` granted direct ledger access? This is an architectural choice worth making explicit. |
| **Memory write only on checkpoint/run-complete** | The diagram only writes to Memory at checkpoint and run-complete. The planning doc implies memory reads/writes can happen during any turn (hot context updates). |

---

### Summary Matrix

| Concept | Diagram | Planning Doc | Artifacts | Gap Location |
|---|:---:|:---:|:---:|---|
| Policy/Sandbox boundary | - | ++ | ++ | Diagram |
| Provider adapter layer | - | ++ | ++ | Diagram |
| RunProfile/requestType | - | ++ | ++ | Diagram |
| Turn loop vs workflow loop | ~ | ++ | ++ | Diagram |
| Specialist/handoff flow | ~ | ++ | + | Diagram |
| Explicit planner state | ~ | ++ | ++ | Diagram |
| Visibility rules | - | ++ | ++ | Diagram |
| Compaction | ~ | ++ | + | Diagram |
| Error/retry/timeout | - | ++ | + | Diagram |
| Evidence Store contract | ++ | ~ | ~ | Doc/Artifacts |
| Artifact Store contract | ++ | ~ | ~ | Doc/Artifacts |
| Act lifecycle (intent→start→finish) | ++ | ~ | ~ | Doc/Artifacts |
| Trace start ordering | ++ | + | + | Consistent |
| Hot/warm/cold memory tiers | - | ++ | ++ | Diagram |

`++` = well-covered, `+` = mentioned, `~` = implicit, `-` = absent