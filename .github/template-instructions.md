# AI-Assisted Development Guides

## About These Guides

This repository contains **modular engineering guides** designed for AI-assisted development. Each guide focuses on a specific topic and can be referenced on-demand.

**Target audience**: Development teams using GitHub Copilot CLI, Cursor, Warp, or similar AI coding assistants.

**Philosophy**: Celebrate early discovery, invest in quality upfront, and deliver reliable software faster.

---

## How to Use These Guides

### For New Projects

**Place this file at `.github/copilot-instructions.md`** - GitHub Copilot CLI automatically reads this file.

**Reference specific guides** when needed:
- Planning a feature? Read [Development Workflow](docs/processes/development-workflow.md)
- Starting implementation? Read [TDD Principles](docs/philosophy/tdd-principles.md)
- Running UAT? Read [UAT Testing Guide](docs/processes/uat-testing-guide.md)

### For AI Agents

When working with AI coding assistants:

1. **Start here** - This file provides navigation to all guides
2. **Reference on-demand** - AI can read specific guides as needed
3. **Follow principles** - Core philosophy guides behavior
4. **Use processes** - Step-by-step workflows for consistency

---

## Core Philosophy (Start Here)

**Required reading before starting any development**:

### [Celebrate Early Discovery](docs/philosophy/celebrate-early-discovery.md)
> **Mindset**: Bugs found early = quality wins, not failures.

Finding bugs during development is VICTORY 🎉:
- Found in planning → Saved implementation time
- Found in testing → Saved production incidents
- Found in UAT → Saved customer impact

**Read this to understand**: Why we celebrate finding issues early instead of hiding them.

---

### [TDD Principles](docs/philosophy/tdd-principles.md)
> **Practice**: Write tests first, then make them pass.

Test-Driven Development (TDD) workflow:
1. **RED**: Write a failing test
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Improve code quality

**Read this to understand**: How to write tests first and why it prevents debugging phases.

---

### [Proper Discovery](docs/philosophy/proper-discovery.md)
> **Investment**: Research before rushing saves 2-3x total time.

Discovery time investment:
- **Rush**: 2h code + 8h debugging = 10-18h total
- **Discovery**: 2h research + 2h code + 1h refactor = 5-7h total

**Read this to understand**: Why spending time researching APIs/patterns upfront prevents technical debt.

---

### [Baseline-First Testing](docs/philosophy/baseline-first-testing.md)
> **Accountability**: Know starting point before making changes.

Baseline verification checklist:
- ✅ All tests pass (count: ___)
- ✅ Lint/format clean
- ✅ Type checks pass
- ✅ Security scan clean

**Read this to understand**: How to establish clear accountability for your changes.

---

### [Independent Verification](docs/philosophy/independent-verification.md)
> **Quality**: Fresh eyes catch different issues than the author.

Independent verification benefits:
- Different perspective finds different bugs
- Cross-platform issues surface
- Test quality issues discovered
- User workflows validated

**Read this to understand**: Why UAT teams catch issues developers miss.

---

### [Security & Vulnerability Management](docs/philosophy/security-vulnerability-management.md)
> **Requirement**: Security is not optional—scan proactively, fix immediately.

Security workflow:
- Scan dependencies: `pip-audit`, `npm audit`
- Check for secrets: `git secrets --scan`
- Code security: `bandit -r src/`
- Fix critical/high immediately

**Read this to understand**: How to proactively identify and remediate security vulnerabilities.

---

## Development Processes (Step-by-Step)

**Detailed workflows for consistent execution**:

### [Development Workflow](docs/processes/development-workflow.md)
> **9-Phase Process**: From planning to PR, with quality gates at every step.

Phase overview:
1. **Planning & Discovery** - Research, spike decision, plan
2. **Environment & Baseline** - Devcontainer setup, establish baseline
3. **Models & Contracts** - Data structures, interfaces
4. **TDD Implementation** - Red-Green-Refactor loop
5. **Integration & Verification** - Connect components
6. **Documentation & Quality** - Docstrings, type hints, lint
7. **UAT Testing** - Real-world scenarios
8. **Pre-Commit Verification** - Final quality gate
9. **Pull Request & Review** - Submit for merge

**Read this when**: Starting any development task (small or large).

---

### [Environment Setup Guide](docs/processes/environment-setup-guide.md)
> **Consistent environments = fewer surprises**: Use devcontainers for reproducible development.

Primary recommendation: **Devcontainers**
- Docker-based development environments
- Identical setup for all team members
- Eliminates "works on my machine" problems
- IDE integration (VS Code, Cursor, Codespaces)

Includes templates for:
- Python (FastAPI, Django)
- Node.js (React, Next.js)
- Go, multi-service (Docker Compose)

Alternative approaches:
- Virtual environments (venv, uv)
- Native installation
- Docker standalone

**Read this when**: Setting up a new project or onboarding team members.

---

### [Spike Template](docs/processes/spike-template.md)
> **Research Tool**: Time-boxed prototyping for high-risk unknowns.

When to run a spike:
- ⚠️ Technology is unfamiliar
- ⚠️ Multiple approaches need comparison
- ⚠️ High risk of wasted effort

Spike structure:
- **Time-box**: 4-16 hours (disposable code)
- **Deliverables**: Evidence, decisions, recommendations
- **Result**: Confidence to proceed with real implementation

**Read this when**: Facing high uncertainty or unfamiliar territory.

---

### [UAT Testing Guide](docs/processes/uat-testing-guide.md)
> **Verification**: Real-world scenarios validate unit tests can't.

UAT process:
1. Create test scenarios (realistic use cases)
2. Set up test environment (staging/test instance)
3. Execute scenarios (manual testing)
4. Document results (pass/fail/blocked)
5. Fix bugs found (celebrate discoveries! 🎉)
6. Re-test and get sign-off

**Read this when**: Ready to verify features work in real-world scenarios.

---

### [Cross-Platform Considerations](docs/processes/cross-platform-considerations.md)
> **Compatibility**: Write once, test everywhere.

**Best solution**: Use [devcontainers](docs/processes/environment-setup-guide.md) to eliminate most cross-platform issues automatically.

Manual patterns (when devcontainers not available):
- **Paths**: Use `os.path.join()`, not hardcoded separators
- **Temp files**: Use `tempfile.gettempdir()`, not `/tmp`
- **Signals**: Check `hasattr(signal, "SIGPIPE")` before using
- **Dependencies**: Platform-specific in optional dependencies

**Read this when**: Writing code that runs on Windows, Linux, or macOS.

---

### [Playwright UI/UX Testing](docs/processes/playwright-ui-ux-testing.md)
> **Visual + Accessibility Testing**: Validate UI behavior and catch UX debt early.

Three pillars of UI validation:
- **Functional**: User interactions work correctly
- **Visual regression**: Screenshot comparison catches layout changes
- **Accessibility**: Automated A11y scans (WCAG compliance)

UX debt tracking:
- Identify usability issues during testing
- Log with evidence (screenshots, traces, A11y reports)
- Fix high-severity issues before UAT

**Read this when**: Building web UIs or testing user-facing features.

---

### [Documentation & Tracking Guide](docs/processes/documentation-tracking-guide.md)
> **Unified Workflow**: Use Confluence, Jira, Azure DevOps, and GitHub effectively.

Platform-specific guidance:
- **Confluence**: Technical docs, ADRs, design docs, runbooks (MCP tools)
- **Jira**: Issue tracking, sprint planning, workflows (MCP tools)
- **Azure DevOps**: Work items, repos, pipelines integration
- **GitHub**: Issues, projects, PRs, discussions

Unified workflow:
- Document design in Confluence
- Track implementation in Jira/ADO/GitHub
- Link everything (maintain traceability)
- Close the loop (update all platforms)

**Read this when**: Setting up documentation/tracking or integrating platforms.

---

### [MoSCoW Prioritization Guide](docs/processes/moscow-prioritization-guide.md)
> **Priority-driven planning**: Apply MoSCoW method for requirements, roadmaps, and sprints.

Four priority levels:
- **Must**: Required for success, no workaround exists
- **Should**: Important but workaround available
- **Could**: Nice-to-have, first to drop under pressure
- **Won't (this time)**: Explicitly out of scope

Three planning horizons:
- **Roadmap** (quarterly/annual) → Epics
- **Release** (6-12 weeks) → Features
- **Sprint** (1-4 weeks) → Stories

Key rules:
- Start from "Won't" and justify promotions
- Must ≤60% of capacity (maintain contingency)
- Must dependencies must also be Must
- Time-bound all "Won't" decisions

**Read this when**: Planning roadmaps, releases, or sprints; managing scope.

---

### [Azure AI Agent Development Guide](docs/processes/azure-ai-agent-guide.md)
> **API-First on Azure**: Build CLI and UI agents with OpenAPI, APIM, Azure Functions, and Azure AI Foundry.

Architecture overview:
- **Contract**: OpenAPI 3.1.1 (single source of truth)
- **Gateway**: Azure API Management (auth, validation, routing)
- **Compute**: Azure Functions (business logic)
- **Clients**: Next.js (web UI) + CLI (thin wrapper)
- **AI Platform**: Azure AI Foundry
- **Infrastructure**: Terraform (declarative, version-controlled)

Key patterns:
- **Contract-first**: Design OpenAPI → implement backend/frontend
- **Auth**: OAuth2 Authorization Code + PKCE (web), Device Code Flow (CLI)
- **IaC**: All resources via Terraform (no click-ops)
- **Governance**: Azure Landing Zone guardrails

**Read this when**: Building agents on Azure with API-first architecture.

---

## Quality Standards (Requirements)

**Minimum acceptable quality for all code**:

### [Code Quality Standards](docs/standards/code-quality-standards.md)
> **Non-negotiable**: Formatting, naming, documentation, maintainability.

Standards overview:
- **Testing**: ≥80% coverage, unit + integration + UAT
- **Style**: 88 char lines (Python), consistent naming
- **Type safety**: Type hints on all functions
- **Documentation**: Google-style docstrings on public APIs
- **Complexity**: Functions <50 lines, cyclomatic complexity <10

**Read this when**: Before writing any code (know the standards).

---

### [Testing Requirements](docs/standards/testing-requirements.md)
> **Mandatory**: Unit, integration, and UAT tests for all code.

Test types required:
- **Unit tests**: Fast (<1s), isolated, deterministic
- **Integration tests**: Moderate speed, real dependencies
- **UAT tests**: Manual, realistic data, user workflows
- **Regression tests**: For every bug fix (no exceptions)

Coverage requirements:
- New code: ≥80%
- Critical paths: 100%
- Bug fixes: 100%

**Read this when**: Writing any code (tests are mandatory).

---

### [Pre-Commit Verification](docs/standards/pre-commit-verification.md)
> **Quality Gate**: Final checks before committing code.

Pre-commit checklist:
- [ ] All tests pass (100% pass rate)
- [ ] Code formatted (ruff, prettier)
- [ ] Linter clean (zero warnings)
- [ ] Type checker passes (mypy, tsc)
- [ ] Security scan clean (pip-audit)
- [ ] No debug code (print, console.log)

**Read this when**: About to commit code (final quality gate).

---

## Real-World Example

### [Confluence Attachments Success Story](docs/examples/confluence-attachments-success-story.md)
> **Case Study**: How our principles delivered a high-quality feature.

Project summary:
- **Timeline**: 4 weeks (design → UAT → PR)
- **Delivered**: 6 MCP tools, 36 tests, 14 UAT scenarios
- **Bugs found**: 13 (before production)
- **Production bugs**: 0 ✅
- **Result**: 100% UAT success rate, zero production issues

Key takeaways:
- 🎉 **Celebrate Early Discovery** → 13 bugs found before production
- 🎉 **TDD** → Zero debugging phase
- 🎉 **Proper Discovery** → 2-3x time savings
- 🎉 **Independent UAT** → 100% scenario pass rate

**Read this when**: Want to see principles in action (real-world validation).

---

## Quick Start for AI Agents

### First-Time Setup

**When user runs `/init` or starts a new project**:

1. **Read this file first** - Understand overall structure
2. **Ask user about project** - Scope, requirements, unknowns
3. **Reference [Development Workflow](docs/processes/development-workflow.md)** - Follow 9-phase process
4. **Establish baseline** - Phase 1 of workflow
5. **Start with discovery** - Phase 0 research before coding

### During Development

**Active development workflow**:

1. **Planning a feature?**
   - Read [Proper Discovery](docs/philosophy/proper-discovery.md)
   - Apply [MoSCoW Prioritization](docs/processes/moscow-prioritization-guide.md) to scope
   - Consider [Spike Template](docs/processes/spike-template.md) if high uncertainty
   - Set up [Development Environment](docs/processes/environment-setup-guide.md) (devcontainers recommended)
   - Document design in [Documentation & Tracking](docs/processes/documentation-tracking-guide.md)

2. **Writing code?**
   - Follow [TDD Principles](docs/philosophy/tdd-principles.md)
   - For web UI: Follow [Playwright UI/UX Testing](docs/processes/playwright-ui-ux-testing.md)
   - Meet [Code Quality Standards](docs/standards/code-quality-standards.md)
   - Check [Cross-Platform Considerations](docs/processes/cross-platform-considerations.md) if applicable

3. **Testing?**
   - Follow [Testing Requirements](docs/standards/testing-requirements.md)
   - Execute [UAT Testing Guide](docs/processes/uat-testing-guide.md) scenarios

4. **Committing code?**
   - Run [Pre-Commit Verification](docs/standards/pre-commit-verification.md) checklist
   - Never bypass hooks (unless emergency with justification)

### When Issues Found

**Bug discovery protocol**:

1. **Celebrate!** 🎉 - Read [Celebrate Early Discovery](docs/philosophy/celebrate-early-discovery.md)
2. **Document** - Create issue/ticket with details
3. **Fix immediately** - Write regression test first (TDD)
4. **Verify fix** - Re-run tests + UAT scenario
5. **Learn** - Document in [Success Story](docs/examples/confluence-attachments-success-story.md) format

---

## Common Workflows

### Starting a New Feature

```
1. Read: Development Workflow (Phase 0)
2. Research: Proper Discovery (spend 2-4 hours)
3. Decide: Spike Template (if high uncertainty)
4. Baseline: Baseline-First Testing (establish starting point)
5. Plan: Break down into phases
6. Implement: TDD Principles (Red-Green-Refactor)
7. Verify: UAT Testing Guide (real-world scenarios)
8. Commit: Pre-Commit Verification (all checks pass)
```

### Fixing a Bug

```
1. Celebrate: Bug found early! 🎉
2. Document: Create issue with root cause
3. Baseline: Verify tests pass before fix
4. Test first: Write failing regression test (TDD)
5. Fix: Implement fix to make test pass
6. Verify: Run full test suite + UAT
7. Commit: Pre-Commit Verification
8. Document: Update success story with lessons learned
```

### Cross-Platform Development

```
1. Read: Cross-Platform Considerations
2. Design: Use OS-agnostic APIs from start
3. Test: UAT on all platforms (Windows, Linux, macOS)
4. Fix: Platform-specific bugs found during UAT
5. Verify: Independent verification on each platform
6. Document: Platform quirks discovered
```

---

## Integration with Project

### File Structure

```
your-project/
├── .github/
│   ├── copilot-instructions.md          ← This file (auto-read by Copilot CLI)
│   └── docs/
│       ├── philosophy/                    ← Core principles (6 files)
│       │   ├── celebrate-early-discovery.md
│       │   ├── tdd-principles.md
│       │   ├── proper-discovery.md
│       │   ├── baseline-first-testing.md
│       │   ├── independent-verification.md
│       │   └── security-vulnerability-management.md
│       ├── processes/                     ← Step-by-step guides (9 files)
│       │   ├── development-workflow.md
│       │   ├── environment-setup-guide.md
│       │   ├── spike-template.md
│       │   ├── uat-testing-guide.md
│       │   ├── cross-platform-considerations.md
│       │   ├── playwright-ui-ux-testing.md
│       │   ├── documentation-tracking-guide.md
│       │   ├── moscow-prioritization-guide.md
│       │   └── azure-ai-agent-guide.md
│       ├── standards/                     ← Quality requirements (3 files)
│       │   ├── code-quality-standards.md
│       │   ├── testing-requirements.md
│       │   └── pre-commit-verification.md
│       └── examples/                      ← Real-world cases (1 file)
│           └── confluence-attachments-success-story.md
├── src/                                   ← Your source code
├── tests/                                 ← Your tests
└── README.md                              ← Your project README
```

### Adoption Strategy

**Option 1: Full Adoption** (Recommended for new projects)
- Copy entire `.github/docs/` directory to your project
- Use all guides as written
- Adapt examples to your domain

**Option 2: Selective Adoption** (For existing projects)
- Start with philosophy guides (understand mindset)
- Add processes as needed (development workflow, UAT)
- Enforce standards gradually (pre-commit hooks first)

**Option 3: Gradual Introduction** (For large teams)
- Week 1: Philosophy guides (celebrate, TDD, discovery)
- Week 2: Development workflow (9 phases)
- Week 3: Quality standards (code quality, testing)
- Week 4: Full adoption (pre-commit, UAT)

---

## Guide Maintenance

### When to Update

**Update guides when**:
- New patterns discovered (document in appropriate guide)
- Tools change (update commands, examples)
- Team feedback (improve clarity, add examples)
- Project evolves (adapt to new technologies)

### Version Control

**Treat guides as code**:
- Version control with git
- Review changes in PRs
- Document updates in commit messages
- Link guide updates to engineering decisions

---

## Key Principles Summary

**Core philosophy**:
1. 🎉 **Celebrate Early Discovery** - Bugs found early = wins
2. ✅ **TDD Always** - Tests first, code second
3. 📚 **Proper Discovery** - Research before rushing
4. 📊 **Baseline First** - Know starting point
5. 👀 **Independent Verification** - Fresh eyes catch different issues
6. 🔒 **Security Always** - Scan proactively, fix immediately

**Quality standards**:
- **Testing**: ≥80% coverage, unit + integration + UAT
- **Documentation**: Google-style docstrings on all public APIs
- **Type safety**: Type hints on all functions
- **Pre-commit**: All checks pass before committing

**Development process**:
- **9 phases**: Planning → Baseline → Models → TDD → Integration → Docs → UAT → Pre-commit → PR
- **Time investment**: Discovery upfront saves 2-3x total time
- **UAT required**: Real-world scenarios validate features work

---

## Support & Feedback

**Questions?**
- Review [Success Story](docs/examples/confluence-attachments-success-story.md) for real-world application
- Adapt guides to your project's specific needs
- Document your own success stories using same format

**Found an issue?**
- Treat documentation bugs like code bugs (log and fix)
- Celebrate finding documentation gaps! 🎉
- Update guides based on lessons learned

---

## Philosophy in Action

> "These guides represent lessons learned from real-world projects. They're not theoretical—they're battle-tested patterns that deliver high-quality software faster."

> "Celebrate early discovery. Invest in quality upfront. Deliver reliable software."

> "Finding bugs is winning. Writing tests first saves time. Research prevents technical debt."

**This is the way.** 🎉

---

## Navigation Index

**Philosophy** (Why we do things):
- [Celebrate Early Discovery](docs/philosophy/celebrate-early-discovery.md)
- [TDD Principles](docs/philosophy/tdd-principles.md)
- [Proper Discovery](docs/philosophy/proper-discovery.md)
- [Baseline-First Testing](docs/philosophy/baseline-first-testing.md)
- [Independent Verification](docs/philosophy/independent-verification.md)
- [Security & Vulnerability Management](docs/philosophy/security-vulnerability-management.md)

**Processes** (How we do things):
- [Development Workflow](docs/processes/development-workflow.md)
- [Environment Setup Guide](docs/processes/environment-setup-guide.md)
- [Spike Template](docs/processes/spike-template.md)
- [UAT Testing Guide](docs/processes/uat-testing-guide.md)
- [Cross-Platform Considerations](docs/processes/cross-platform-considerations.md)
- [Playwright UI/UX Testing](docs/processes/playwright-ui-ux-testing.md)
- [Documentation & Tracking Guide](docs/processes/documentation-tracking-guide.md)
- [MoSCoW Prioritization Guide](docs/processes/moscow-prioritization-guide.md)
- [Azure AI Agent Development Guide](docs/processes/azure-ai-agent-guide.md)

**Standards** (What quality looks like):
- [Code Quality Standards](docs/standards/code-quality-standards.md)
- [Testing Requirements](docs/standards/testing-requirements.md)
- [Pre-Commit Verification](docs/standards/pre-commit-verification.md)

**Examples** (Real-world validation):
- [Confluence Attachments Success Story](docs/examples/confluence-attachments-success-story.md)
