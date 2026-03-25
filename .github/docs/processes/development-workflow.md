# Development Workflow

> **9-Phase Process**: From planning to PR, with built-in quality gates at every step.

---

## Overview

This workflow integrates all our core principles into a step-by-step process:

```
Phase 0: Planning & Discovery
Phase 1: Environment & Baseline
Phase 2: Models & Contracts (if applicable)
Phase 3: TDD Implementation Loop
Phase 4: Integration & Verification
Phase 5: Documentation & Quality
Phase 6: UAT (User Acceptance Testing)
Phase 7: Pre-Commit Verification
Phase 8: Pull Request & Review
```

---

## Phase 0: Planning & Discovery

**Goal**: Understand requirements, research unknowns, plan approach.

### Tasks

- [ ] **Define scope**: What are we building? What's in/out of scope?
- [ ] **Research unknowns**: APIs, libraries, patterns
  * Spend 2-4 hours researching if unfamiliar domain
  * Document findings (avoid guessing)
- [ ] **Decide if spike needed**: High-risk unknowns? Multiple approaches? (See [Spike Template](spike-template.md))
- [ ] **Break down work**: Phases, milestones, tasks
- [ ] **Identify risks**: Technical challenges, dependencies, blockers
- [ ] **Set success criteria**: How will we know it's done?

### Spike Decision Point

**Run a spike if**:
- Technology is unfamiliar (new API, library, pattern)
- Multiple implementation approaches need comparison
- High risk of wasted effort without validation
- Architecture decision needs evidence

**Skip spike if**:
- Similar work done before (proven patterns)
- Requirements and approach are clear
- Low risk, straightforward implementation

(See [When to Run a Spike](spike-template.md) for detailed guidance)

### Discovery Checklist

- [ ] Read official documentation
- [ ] Review existing implementations
- [ ] Check for known issues/bugs
- [ ] Understand authentication/authorization
- [ ] Identify platform-specific quirks
- [ ] Document assumptions and decisions

**Output**: Plan document with phases, tasks, success criteria.

---

## Phase 1: Environment & Baseline

**Goal**: Set up dev environment, establish baseline (tests/lint pass before changes).

### Tasks

- [ ] **Set up development environment**:
  * **Recommended**: Use [devcontainer](environment-setup-guide.md) for consistent environment
  * **Alternative**: Install dependencies locally (`pip install -e '.[dev]'`, `npm install`)
- [ ] **Configure environment**: `.env` files, API keys (use `.env.example`)
- [ ] **Set up pre-commit hooks**: `pre-commit install`
- [ ] **Run baseline tests**: `pytest`, `npm test`, etc.
  * **Expected**: All existing tests pass ✅
  * **If failures**: Not your responsibility to fix (document and move on)
- [ ] **Run baseline lint/type checks**: `ruff check`, `mypy`, `eslint`, etc.
  * **Expected**: All checks pass ✅
  * **If failures**: Not your responsibility (unless blocking your work)
- [ ] **Security scan**: `pip-audit`, `npm audit`, `snyk test`
  * **Critical/High vulnerabilities**: Fix immediately before starting
  * **Medium/Low**: Document for later (don't block)
- [ ] **Create feature branch**: `git checkout -b feature/your-feature`
- [ ] **Document baseline**: "Tests: 247 passed, Lint: Clean, Security: 0 high/critical"

### Environment Setup Decision

**Use devcontainers if**:
- Multi-person project (consistency matters)
- Cross-platform team (Windows + macOS + Linux)
- Complex dependencies (database, Redis, etc.)
- AI agent development (GitHub Copilot CLI, Cursor)

**Use local environment if**:
- Single-person project (no coordination needed)
- Simple dependencies (pure Python/Node)
- Docker not available (corporate restrictions)

**See**: [Environment Setup Guide](environment-setup-guide.md) for detailed instructions.

### Baseline Verification

**Why this matters**: Establishes accountability. If tests fail later, you know it's from your changes.

**Baseline checklist**:
```
✅ Development environment ready (devcontainer or local)
✅ All tests pass (count: ___)
✅ Lint/format clean (tools: ___)
✅ Type checks pass (mypy, pyright, tsc)
✅ No high/critical security vulnerabilities
✅ Feature branch created
```

**Output**: Baseline report + clean feature branch.

---

## Phase 2: Models & Contracts (If Applicable)

**Goal**: Define data structures and interfaces before implementation.

### Tasks

- [ ] **Define data models**: Pydantic, TypeScript interfaces, Golang structs, etc.
- [ ] **Write model tests**: Validation, serialization, deserialization
  * Test success cases (valid data)
  * Test failure cases (invalid data, missing fields)
- [ ] **Run tests**: All model tests pass ✅
- [ ] **Define protocols/interfaces**: Contracts for dependencies
- [ ] **Document models**: Docstrings, type hints, examples
- [ ] **Commit**: `git commit -m "feat: Add data models and protocols"`

### Example (Python)

```python
# models.py
class User(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

# test_models.py
def test_user_valid():
    user = User(id="1", name="Alice", email="alice@example.com", created_at=datetime.now())
    assert user.id == "1"

def test_user_invalid_email():
    with pytest.raises(ValidationError):
        User(id="1", name="Alice", email="not-an-email", created_at=datetime.now())
```

**Output**: Models + tests, all passing.

---

## Phase 3: TDD Implementation Loop

**Goal**: Implement functionality using Test-Driven Development.

### RED → GREEN → REFACTOR Cycle

**For each feature/function**:

1. **RED**: Write a failing test
   ```python
   def test_upload_file():
       result = uploader.upload("file.txt")
       assert result["success"] is True
   ```
   
2. **Run test**: Verify it fails ❌ (because feature not implemented)
   ```bash
   pytest -v test_uploader.py::test_upload_file
   # Expected: FAILED (function doesn't exist yet)
   ```

3. **GREEN**: Write minimal code to make test pass
   ```python
   def upload(filename: str) -> dict[str, Any]:
       return {"success": True}  # Simplest implementation
   ```

4. **Run test**: Verify it passes ✅
   ```bash
   pytest -v test_uploader.py::test_upload_file
   # Expected: PASSED
   ```

5. **REFACTOR**: Improve code quality (don't change behavior)
   ```python
   def upload(filename: str) -> dict[str, Any]:
       # Add error handling, logging, validation
       if not os.path.exists(filename):
           return {"success": False, "error": "File not found"}
       return {"success": True}
   ```

6. **Run test**: Verify still passes ✅ (refactoring didn't break anything)

7. **Repeat**: Next test, next feature

### TDD Best Practices

- ✅ **Write test FIRST** (before implementation code)
- ✅ **Test one thing** (each test has single responsibility)
- ✅ **Make CODE pass TEST** (not test pass code)
- ✅ **Red-Green-Refactor** (always verify failure before success)
- ✅ **Run tests frequently** (after every small change)

**Output**: Fully tested, working functionality.

---

## Phase 4: Integration & Verification

**Goal**: Integrate with existing codebase, verify no conflicts.

### Tasks

- [ ] **Integration points**: Connect new code to existing systems
- [ ] **Integration tests**: Test interaction with other components
  ```python
  def test_integration_with_existing_system():
      # Test that new feature works with existing code
      result = system.process_with_new_feature()
      assert result["status"] == "success"
  ```
- [ ] **Run all tests**: `pytest` (not just new tests)
  * **Expected**: All tests pass ✅ (including pre-existing tests)
  * **If failures**: Your changes broke something—fix it
- [ ] **Test baseline maintained**: Original test count + new tests
- [ ] **No method conflicts**: Verify no naming collisions
- [ ] **Documentation updated**: If APIs changed

### Integration Checklist

```
✅ New code integrated with existing codebase
✅ Integration tests written and passing
✅ All tests pass (baseline + new)
✅ No naming conflicts or duplicates
✅ Dependencies properly injected
✅ Error handling consistent with codebase
```

**Output**: Integrated feature, all tests passing.

---

## Phase 5: Documentation & Quality

**Goal**: Document everything, ensure code quality standards met.

### Tasks

- [ ] **Docstrings**: All public APIs documented (Google-style, JSDoc, etc.)
  ```python
  def upload_file(filepath: str, timeout: int = 30) -> dict[str, Any]:
      """Upload a file to the server.
      
      Args:
          filepath: Path to file to upload
          timeout: Request timeout in seconds (default: 30)
      
      Returns:
          Dictionary with 'success' boolean and optional 'error' message
      
      Raises:
          FileNotFoundError: If filepath doesn't exist
          TimeoutError: If upload exceeds timeout
      """
  ```

- [ ] **Type hints**: All functions have complete type annotations
- [ ] **Comments**: Clarify complex logic (but prefer self-documenting code)
- [ ] **README/docs**: Update if new features/APIs added
- [ ] **Examples**: Add usage examples for public APIs
- [ ] **Changelog**: Document changes (if project uses one)

### Quality Checks

- [ ] **Run linter**: `ruff check`, `eslint`, etc. (zero warnings)
- [ ] **Run formatter**: `ruff format`, `prettier`, etc. (consistent style)
- [ ] **Run type checker**: `mypy`, `pyright`, `tsc` (zero errors)
- [ ] **Check coverage**: `pytest --cov` (aim for >80% on new code)
- [ ] **Review code**: Self-review for obvious issues

**Output**: Well-documented, high-quality code.

---

## Phase 6: UAT (User Acceptance Testing)

**Goal**: Verify feature works in real-world scenarios with realistic data.

### UAT Process

- [ ] **Create test scenarios**: Real use cases (not just unit test cases)
- [ ] **Set up test environment**: Staging, test instance, etc.
- [ ] **Execute scenarios**: Manual testing with realistic data
- [ ] **Document results**: Record what worked, what didn't
- [ ] **Fix bugs found**: Celebrate early discovery! 🎉
- [ ] **Re-run scenarios**: Verify fixes work
- [ ] **Get stakeholder sign-off**: Demo to product owner/users

### UAT Template

```markdown
## UAT Scenario: Upload Large File

**Goal**: Verify large files (>100MB) upload successfully

**Steps**:
1. Select 150MB file
2. Call upload API
3. Verify progress reporting
4. Verify upload completes
5. Verify file integrity

**Expected**:
- Progress updates received
- Upload completes within 60 seconds
- File checksum matches original

**Actual**:
- ✅ Progress updates working
- ❌ Timeout after 30 seconds (BUG FOUND 🎉)
- ⏳ File integrity not verified (after fix)

**Bugs Found**: #42 - Timeout too short for large files
**Status**: Fixed, re-tested, passed ✅
```

(See [UAT Testing Guide](uat-testing-guide.md) for detailed templates)

**Output**: UAT report, bugs found and fixed.

---

## Phase 7: Pre-Commit Verification

**Goal**: Final quality gate before committing code.

### Pre-Commit Checklist

- [ ] **All tests pass**: `pytest -v` (100% pass rate)
- [ ] **Lint clean**: `ruff check` (zero warnings)
- [ ] **Format clean**: `ruff format --check` (zero changes)
- [ ] **Type check clean**: `mypy` (zero errors)
- [ ] **Security scan clean**: `pip-audit` (no critical/high)
- [ ] **Pre-commit hooks pass**: `pre-commit run --all-files`
- [ ] **No debug code**: No `print()`, `console.log()`, `debugger` statements
- [ ] **No TODOs**: All TODOs addressed or documented as tech debt
- [ ] **Git status clean**: Only intended files staged

### Running Pre-Commit

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Expected output:
# trim trailing whitespace...................Passed
# fix end of files...........................Passed
# check yaml.................................Passed
# ruff-format................................Passed
# ruff.......................................Passed
# mypy.......................................Passed
```

### Commit Message

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Examples**:
```bash
git commit -m "feat(confluence): Add attachment upload operation"

git commit -m "fix: Handle timeout for large file uploads

Increased timeout from 30s to 120s for files >100MB.
Found during UAT testing.

Fixes: #42
"

git commit -m "docs: Update API reference with examples"
```

(See [Pre-Commit Verification](../standards/pre-commit-verification.md) for detailed checklist)

**Output**: Clean commit ready to push.

---

## Phase 8: Pull Request & Review

**Goal**: Submit changes for review, address feedback.

### PR Preparation

- [ ] **Push branch**: `git push origin feature/your-feature`
- [ ] **Create PR**: On GitHub/GitLab/etc.
- [ ] **Fill PR template**: Description, changes, testing, checklist
- [ ] **Link issues**: Reference related issues/tickets
- [ ] **Request reviewers**: Tag appropriate team members
- [ ] **Wait for CI**: Ensure all checks pass ✅

### PR Description Template

```markdown
## Description
Brief summary of changes (1-2 sentences)

Fixes: #123

## Changes
- Added feature X
- Updated documentation
- Fixed bug Y

## Testing
- [x] Unit tests (51 new tests, 100% pass rate)
- [x] Integration tests (5 tests, all passing)
- [x] UAT (7 scenarios, all passing)
- [x] Cross-platform verified (Windows, Linux, macOS)

## Documentation
- [x] Docstrings added
- [x] README updated
- [x] API reference updated

## Checklist
- [x] Tests pass
- [x] Lint/format clean
- [x] Documentation updated
- [x] No breaking changes (or documented)
```

### Review Process

- [ ] **Address feedback**: Make requested changes
- [ ] **Push updates**: `git push` (updates PR automatically)
- [ ] **Re-request review**: After addressing feedback
- [ ] **Get approval**: Wait for reviewer approval ✅
- [ ] **Merge**: Squash/merge/rebase per project standards

**Output**: Merged PR, feature in main branch.

---

## Workflow Summary (Quick Reference)

```
Phase 0: Planning & Discovery
├─ Define scope, research unknowns
├─ Decide if spike needed
└─ Create plan with phases/tasks

Phase 1: Environment & Baseline
├─ Install dependencies
├─ Run baseline tests (must pass)
├─ Security scan (fix critical/high)
└─ Create feature branch

Phase 2: Models & Contracts (if needed)
├─ Define data models
├─ Write model tests
└─ Commit models

Phase 3: TDD Implementation
├─ Write failing test (RED)
├─ Implement to pass (GREEN)
├─ Refactor code (REFACTOR)
└─ Repeat for each feature

Phase 4: Integration & Verification
├─ Integrate with existing code
├─ Write integration tests
└─ Verify all tests pass

Phase 5: Documentation & Quality
├─ Add docstrings/comments
├─ Run lint/format/type checks
└─ Update README/docs

Phase 6: UAT Testing
├─ Create test scenarios
├─ Execute with real data
├─ Fix bugs found (celebrate!)
└─ Get stakeholder sign-off

Phase 7: Pre-Commit Verification
├─ All tests pass
├─ Lint/format/type checks clean
├─ Security scan clean
└─ Pre-commit hooks pass

Phase 8: Pull Request & Review
├─ Create PR with description
├─ Address reviewer feedback
├─ Get approval
└─ Merge to main
```

---

## Key Principles Throughout

**1. Celebrate Early Discovery** 🎉
- Bugs found = wins (at every phase)
- Document and fix immediately
- Don't hide or defer issues

**2. Test-Driven Development**
- Tests first, then code
- Red → Green → Refactor
- High test coverage

**3. Proper Discovery**
- Research before implementing
- Spike when uncertain
- Document decisions

**4. Baseline-First**
- Know starting point
- Measure changes
- Maintain clean baseline

**5. Independent Verification**
- UAT catches what unit tests miss
- Cross-platform testing
- Fresh eyes find different issues

**6. Security Always**
- Scan at Phase 1 (baseline)
- Scan at Phase 7 (pre-commit)
- Fix critical/high immediately

---

## Time Investment

**Estimated time per phase** (varies by feature size):

| Phase | Time | Notes |
|-------|------|-------|
| Phase 0 | 1-4 hours | Longer if spike needed |
| Phase 1 | 0.5-1 hour | One-time setup |
| Phase 2 | 0.5-2 hours | If models needed |
| Phase 3 | 2-8 hours | Varies by complexity |
| Phase 4 | 1-2 hours | Integration + tests |
| Phase 5 | 1-2 hours | Documentation + quality |
| Phase 6 | 1-4 hours | UAT scenarios |
| Phase 7 | 0.5-1 hour | Final verification |
| Phase 8 | 1-2 hours | PR + review |
| **Total** | **8-26 hours** | Small to medium feature |

**Investment pays off**:
- Fewer bugs in production
- Easier maintenance
- Faster future changes
- Higher code quality

---

**Related**:
- [Spike Template](spike-template.md) - When and how to run spikes
- [UAT Testing Guide](uat-testing-guide.md) - UAT process and templates
- [TDD Principles](../philosophy/tdd-principles.md) - Test-driven development details
- [Celebrate Early Discovery](../philosophy/celebrate-early-discovery.md) - Finding bugs early
- [Pre-Commit Verification](../standards/pre-commit-verification.md) - Final quality gate
