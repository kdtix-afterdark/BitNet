# Task: TASK-LAH-020 Clean-Lab Apple Silicon Bootstrap and GGUF Dependency Spike

> **Issue Type**: Task
> **GitHub Project**: [BitNet Enhancements](https://github.com/orgs/kdtix-afterdark/projects/2)
> **Labels**: `enhancement`, `created by codex`, `planning`, `agent-harness`, `uat`, `readiness`, `apple-silicon`, `bootstrap`, `found in UAT`, `spike`
> **Blocked By**: None
> **Blocks**: [TASK-LAH-016](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-016_end_to_end_uat_and_readiness_checklist.md)

---

> **Status**: To Do
> **Priority**: High
> **Parent Story**: [US-LAH-008](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/US-LAH-008_modern_stack_readiness_and_uat.md)
> **Area**: 🔍 Research/Spike
> **Estimate**: 4 hrs

---

## Summary

Run a time-boxed spike to determine the intended clean-lab bootstrap contract for Apple Silicon Metal UAT, including the correct `gguf` dependency model, supported Python version expectations, and whether the current one-step `setup_env.py` flow matches first-class Apple Silicon support claims.

---

## Context

- **Parent Story AC**: UAT scenario completeness and rollout evidence
- **Preceding Task**: [TASK-LAH-004](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-004_context_compiler_assembly_and_regression_coverage.md)
- **Blocking Tasks**: [TASK-LAH-016](/Users/ckreager/repos/kdtix/LLMs/BitNet/docs/plans/artifacts/local_llm_agent_harness_modern_stacks/TASK-LAH-016_end_to_end_uat_and_readiness_checklist.md)

---

## I Know I Am Done When

- [ ] The clean-lab Apple Silicon bootstrap contract is documented end to end, including the expected model-download, conversion, and build flow.
- [ ] The intended `gguf` dependency model is explicit: vendored local path, submodule path, pip dependency, or supported fallback order.
- [ ] Python version expectations and packaging constraints for a fresh lab are documented with evidence.
- [ ] The spike records a decision, confidence level, and follow-on implementation task(s) instead of merging speculative bootstrap fixes.

---

## Implementation Notes

### Spike Charter

- **Question 1:** What is the intended source of truth for `gguf` during clean-lab model conversion on this repo?
- **Question 2:** Is `setup_env.py` intended to be the authoritative one-step Apple Silicon bootstrap path, or is the explicit codegen + CMake path the supported contract for UAT?
- **Question 3:** Are Python 3.13.x environments officially supported for clean-lab model download and conversion, and if not, what version boundary is required?
- **Out of scope:** Fixing the issue during the spike unless a minimal, fully evidenced follow-on task is created and separately approved.

### Evidence to Gather

| Evidence | Source | Why It Matters |
| --- | --- | --- |
| Upstream Apple Silicon guidance | `Eddie-Wang1120/llama.cpp` README at submodule commit `1f86f058` | Confirms first-class support expectations |
| Local import graph for `gguf` | `setup_env.py`, `utils/convert*.py`, vendored `gguf-py` paths | Determines the real dependency contract |
| Clean-lab packaging failures | `logs/install_gguf.log` and reproducible Python 3.13.x runs | Separates toolchain problems from design problems |
| Supported bootstrap documentation | `TASK-LAH-004`, `docs/known_good_metal_build.md`, `README.md` | Shows whether docs and code agree |

### Commands / Scripts

```text
python3 setup_env.py --help
python3 -m unittest discover -s tests -v
python3 setup_env.py --backend metal --build-dir build-metal --model-dir models --hf-repo microsoft/BitNet-b1.58-2B-4T
```

---

## Constraints

- Do not merge bootstrap code changes as part of this spike unless they are backed by documented design intent and a failing regression test.
- Do not assume that a workaround which succeeds locally is the intended product contract for a clean lab.
- Preserve the distinction between Apple Silicon first-class runtime support and Python packaging/tooling support.

---

## Verification

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Trace `gguf` imports and bootstrap steps from docs through code | The real dependency contract is documented with no ambiguity |
| 2 | Reproduce the clean-lab flow on Apple Silicon with Python 3.13.x | The specific failure boundary is captured with logs and environment details |
| 3 | Compare current behavior to upstream/readme expectations | The spike ends with a clear decision and follow-on backlog item(s) |

---

## Notes / Findings

- Triggered by repeated clean-lab bootstrap failures during PR 37 Apple Silicon UAT preparation.
- Created intentionally as a spike after confidence dropped in patch-first iteration.

---

_Created: 2026-03-24_
_Assignee: TBD_
_Parent Story: US-LAH-008_
