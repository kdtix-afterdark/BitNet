# Sprint Spike Template

Use this template to run a **time-boxed spike** that produces **knowledge and a decision**, not production code. Spikes are most valuable for reducing **excess uncertainty** on high-risk / complex work (the “long pole”) while avoiding endless refactoring loops.
This template is aligned with:

- James Shore’s guidance to run **small, isolated experiments** (often as a tiny program or test), intentionally skipping production concerns and treating spike code as **disposable or documentation—not production**.
- Mike Cohn’s guidance that spikes are **time-boxed research activities** that help teams make better decisions, update estimates, and should be used **sparingly** for excess uncertainty.

---

## Spike charter

- **Spike title:** `<short, searchable name>`
- **Spike ID / ticket:** `<link or key>`
- **Related epic / story:** `<link or key>`
- **Owner (DRI):** `<name>`
- **Sponsor / requester (PO/PM/Tech Lead):** `<name>`
- **Target sprint / iteration:** `<sprint>`
- **Decision deadline:** `<date/time>` (when we must decide / unblock)

### Why are we spiking?

- **Long pole / risk statement:** `<1–2 sentences on what is risky/unknown>`
- **Uncertainty type(s):** (check all that apply)
  - [ ] Feasibility (can it work at all?)
  - [ ] Performance / scalability (p95/p99, throughput, memory, cost)
  - [ ] Integration / compatibility (APIs, SDKs, versions, auth, infra)
  - [ ] Architecture / design trade-off (approach A vs B)
  - [ ] Security / compliance (threat model, controls, data handling)
  - [ ] UX / workflow (user path, information architecture)
  - [ ] Build vs buy / vendor fit
- **What makes this “excess uncertainty” (not normal ambiguity)?** `<1–3 bullets>`

---

## Spike question(s)

Write questions that can be answered with working code, measurement, or concrete evidence.

1. **Q1:** `<example: Can approach X meet p95 < 200ms for N=50k records?>`
2. **Q2 (optional):** `<example: Is library Y compatible with runtime Z and our deployment model?>`
3. **Out of scope (explicitly):** `<what we are not trying to learn/solve in this spike>`

---

## Hypotheses and success criteria

For each question, specify what “good enough” looks like to exit the spike.

- **H1:** `<statement>`
  - **Evidence we will accept:** `<benchmark, prototype output, test, docs, etc.>`
  - **Success threshold:** `<numbers/conditions>`
  - **Failure threshold:** `<numbers/conditions>`
- **H2 (optional):** `<statement>`

---

## Timebox and constraints

- **Timebox:** `<e.g., 4–16 hours / 1–2 days>` (fixed; stop when it expires)
- **People:** `<names/roles>`
- **Environment:** `<local/dev/stage; hardware class; cloud region; etc.>`

### Spike code policy (prevents refactoring churn)

- [ ] **Default: throwaway spike.** Keep code isolated (e.g., `spikes/` folder or separate branch/repo). Do **not** merge spike code into production.
- [ ] Use shortcuts freely: hardcode inputs, ignore UI, ignore edge cases, skip “clean code” polish—only answer the question.
- [ ] If a **design spike** requires touching production code, start from a clean commit and **do not** commit spike changes to the mainline. Capture learnings in notes/ADR.

---

## Experiment design

### Options / approaches to compare

- **Approach A:** `<brief>`
- **Approach B:** `<brief>`
- **Approach C (optional):** `<brief>`

### Test harness and instrumentation

- **Dataset / fixtures:** `<size, shape, source>`
- **Workload model:** `<requests/sec, concurrency, input distribution>`
- **Metrics to capture:** (examples)
  - [ ] Latency (p50/p95/p99)
  - [ ] Throughput
  - [ ] Memory/CPU
  - [ ] Error rate / correctness checks
  - [ ] Operational complexity (deployment, migrations, observability)
  - [ ] Cost (cloud resources, licensing)
- **How we will measure:** `<tooling; scripts; profiler; logs; benchmark runner>`

### Execution steps

1. `<setup>`
2. `<implement smallest working prototype/test>`
3. `<run measurements>`
4. `<analyze results and compare options>`
5. `<document learnings + recommendation>`

---

## Results

### Evidence collected

- **Key outputs:** `<links to logs, charts, benchmark results, prototype branch, screenshots>`
- **What surprised us:** `<bullets>`
- **What remains unknown:** `<bullets>`

### Findings by question

- **Q1 answer:** `<concise>`
  - **Data:** `<numbers / evidence>`
  - **Confidence:** `<low/med/high> (why?)`
- **Q2 answer (optional):** `<concise>`

---

## Decision and follow-on work

### Decision

- **Decision made:** `<choose A/B/C, build vs buy, defer, stop, invest more>`
- **Rationale (2–5 bullets):** `<why>`
- **Decision maker(s):** `<names>`
- **Date:** `<date>`

### Follow-on backlog items

Convert spike learnings into concrete work items to avoid “prototype limbo.”

- [ ] `<story/task 1>` — estimate: `<points/hours>`
- [ ] `<story/task 2>` — estimate: `<points/hours>`
- [ ] `<risk mitigation task>` — estimate: `<points/hours>`

### Exit criteria (the spike is “done” when)

- [ ] Timebox is exhausted **or** questions are answered sufficiently.
- [ ] A decision is recorded (ADR/notes) and communicated.
- [ ] Follow-on items are created/updated with improved estimates.
- [ ] Spike code is discarded or archived as documentation (not merged into prod).

---

## References (concept framing)

- James Shore, “Spike Solutions” (The Art of Agile Development) — small, isolated experiments; shortcut-friendly; spike code is not production. (<https://www.jamesshore.com/v2/books/aoad1/spike_solutions>)
- Mike Cohn (Mountain Goat Software), “Agile Spikes Deliver Knowledge So Teams Can Deliver Products” — time-boxed research to reduce excess uncertainty and improve decisions/estimates; avoid overuse. (<https://www.mountaingoatsoftware.com/blog/spikes>)
