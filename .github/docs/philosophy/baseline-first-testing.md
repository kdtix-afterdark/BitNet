# Baseline-First Testing

> **Core Principle #4**: Establish baseline before adding new functionality.

---

## The Philosophy

**Approach**: Know your starting point before making changes.

**Why it matters**:
- Know exactly what your changes affected
- Catch regressions immediately
- Clear accountability for new failures
- Easier debugging and rollback
- Confidence in what you're changing

---

## The Baseline-First Process

### Steps

**1. Run Existing Tests** (Establish Baseline)
```bash
# Before making ANY changes
pytest

# Record results
# Example: 1217 passed, 159 skipped, 0 failed ← BASELINE
```

**2. Document Baseline**
```markdown
## Baseline (2026-02-06)
- Passed: 1217
- Skipped: 159
- Failed: 0
- Coverage: 94%
```

**3. Add New Tests** (For your feature)
```bash
# Write tests for new feature
# tests/unit/test_new_feature.py (36 new tests)
```

**4. Implement Feature** (Make new tests pass)
```bash
# Implement feature
# src/new_feature.py

# Run tests again
pytest

# New results: 1253 passed (1217 + 36), 159 skipped, 0 failed
```

**5. Verify Baseline** (Ensure existing tests still pass)
```bash
# Compare to baseline
# Baseline: 1217 passed
# Current:  1253 passed (1217 original + 36 new)
# ✅ All baseline tests still passing
```

---

## Why Baseline-First?

### Problem Without Baseline

```
Make changes → Run tests → 5 tests fail
→ Which failures are from your changes?
→ Which were already failing?
→ Unclear accountability
→ Difficult debugging
```

**Result**: Wasted time investigating pre-existing failures

### Solution With Baseline

```
Run tests first → 2 tests already failing (baseline)
→ Make changes → Run tests → 7 tests fail
→ 2 were already failing (not your problem)
→ 5 new failures from your changes (investigate these)
→ Clear accountability
→ Focused debugging
```

**Result**: Know exactly what you broke

---

## Real-World Example

### Confluence Attachments Feature

**Phase 0: Baseline Established**
```bash
$ pytest
1217 passed, 159 skipped, 0 failed in 45.2s
Coverage: 94%
```

**Documented**: "Starting from clean baseline, zero failures"

**Phase 2: After Adding 36 Unit Tests**
```bash
$ pytest
1253 passed, 159 skipped, 0 failed in 48.5s
Coverage: 96%
```

**Analysis**:
- ✅ All 36 new tests passing
- ✅ All 1217 baseline tests still passing
- ✅ No regressions introduced
- ✅ Coverage improved (+2%)

**Phase 5: iOS Cross-Platform Testing**

Baseline re-established on iOS:
```bash
$ pytest  # iOS environment
1248 passed, 159 skipped, 5 failed
```

**Analysis**:
- ❌ 5 tests failing on iOS
- ✅ Clear: These 5 are cross-platform issues
- ✅ Not general bugs, platform-specific
- ✅ Focused investigation on these 5

**Result**: Fixed 5 cross-platform issues in hours because baseline made them obvious

---

## When to Establish Baseline

### 1. Before Starting New Work
```bash
# Day 1 of new feature
git checkout -b feature/new-feature
pytest  # ← Baseline
# Record results, begin work
```

### 2. Before Refactoring
```bash
# Before refactoring legacy code
pytest  # ← Baseline (may have existing failures)
# Document: "Starting with 3 known failures in legacy code"
# Refactor
pytest  # ← Verify baseline maintained
```

### 3. New Platform/Environment
```bash
# Testing on new OS
pytest  # ← Baseline for this platform
# Document platform-specific baseline
```

### 4. After Dependency Updates
```bash
# Before updating dependencies
pytest  # ← Baseline

# Update dependencies
pip install --upgrade package

# After update
pytest  # ← Compare to baseline
# Any new failures = dependency issue
```

### 5. New Team Member Onboarding
```bash
# New developer joins
pytest  # ← Verify their environment matches baseline
# Ensures setup is correct
```

---

## Baseline Documentation

### Template

```markdown
## Test Baseline: [Feature Name]

**Date**: 2026-02-06
**Branch**: feature/attachments
**Environment**: 
- OS: Windows 11
- Python: 3.11.5
- Key packages: pytest 8.0, atlassian-python-api 3.41

**Baseline Results**:
```bash
$ pytest
1217 passed, 159 skipped, 0 failed in 45.2s
Coverage: 94%
```

**Known Issues**:
- 159 integration tests skipped (require live API)
- No failures in baseline

**Next Steps**:
- Add 36 unit tests for AttachmentsMixin
- Target: 100% coverage for new code
- Expected: 1253 passed after implementation
```

### Commit Message

```bash
git commit -m "test: Establish baseline before implementing attachments

Baseline: 1217 passed, 159 skipped, 0 failed
Coverage: 94%

Starting point for attachment operations feature."
```

---

## Baseline in CI/CD

### Track Baseline in Pipeline

```yaml
# .github/workflows/test.yml

- name: Run tests and establish baseline
  run: |
    pytest --cov --json-report
    
- name: Compare to previous baseline
  run: |
    python scripts/compare_baseline.py \
      --current results.json \
      --baseline baseline.json
    
- name: Fail if regressions detected
  run: |
    if [ $REGRESSION_COUNT -gt 0 ]; then
      echo "❌ Regressions detected: $REGRESSION_COUNT tests"
      exit 1
    fi
```

### Baseline Tracking Script

```python
# scripts/compare_baseline.py
def compare_baselines(current, baseline):
    """Compare test results to baseline."""
    new_failures = set(current.failures) - set(baseline.failures)
    fixed_failures = set(baseline.failures) - set(current.failures)
    
    if new_failures:
        print(f"❌ New failures: {len(new_failures)}")
        for test in new_failures:
            print(f"  - {test}")
        return False
    
    if fixed_failures:
        print(f"🎉 Fixed failures: {len(fixed_failures)}")
        for test in fixed_failures:
            print(f"  - {test}")
    
    print(f"✅ Baseline maintained")
    return True
```

---

## Common Scenarios

### Scenario 1: Baseline Has Failures

**Situation**: Inherited codebase with failing tests

```bash
$ pytest
1200 passed, 159 skipped, 17 failed
```

**Action**:
1. **Document baseline**: "Starting with 17 known failures"
2. **Separate concerns**: 
   - Track the 17 as technical debt
   - Your work: Don't add more failures
3. **Success criteria**: Maintain or reduce failure count

```markdown
## Baseline

**Known Failures (17)**: 
- test_legacy_feature_x (3 tests)
- test_old_api_y (14 tests)

**Your Work**:
- Add new feature Z
- Do not increase failure count
- Bonus: Fix legacy failures if time permits
```

### Scenario 2: Flaky Tests

**Situation**: Tests pass/fail intermittently

```bash
# Run 1: 1217 passed, 0 failed
# Run 2: 1215 passed, 2 failed (different 2 tests)
# Run 3: 1214 passed, 3 failed (different 3 tests)
```

**Action**:
1. **Identify flaky tests**: Run multiple times
2. **Document as baseline issue**: "5 tests are flaky"
3. **Track separately**: Don't let flaky tests hide real failures
4. **Fix flaky tests**: High priority (undermines confidence)

```python
# Mark flaky tests
@pytest.mark.flaky(reruns=3)
def test_sometimes_fails():
    pass
```

### Scenario 3: Cross-Platform Baseline

**Situation**: Different platforms have different baselines

```markdown
## Platform Baselines

**Windows**:
- 1253 passed, 159 skipped, 0 failed

**Linux**:
- 1253 passed, 159 skipped, 0 failed

**macOS**:
- 1250 passed, 159 skipped, 3 failed
- Known macOS failures:
  - test_signal_handling (SIGPIPE difference)
  - test_file_permissions (Unix vs Windows)
  - test_timezone_handling (tzdata packaging)
```

**Action**: Document per-platform baselines, track separately

---

## Best Practices

### ✅ DO

- **Run tests before starting work** (establish baseline)
- **Document baseline** (commit message, notes, or wiki)
- **Re-establish baseline** (new environment, platform, or major changes)
- **Track baseline in CI/CD** (automated comparison)
- **Separate new failures from baseline** (clear accountability)
- **Fix flaky tests immediately** (don't let them hide real issues)
- **Update baseline** (when intentionally fixing legacy failures)

### ❌ DON'T

- **Don't skip baseline** ("I'll just fix whatever breaks")
- **Don't ignore existing failures** (document them)
- **Don't assume clean baseline** (verify first)
- **Don't let flaky tests persist** (fix or mark as flaky)
- **Don't mix concerns** (your work vs pre-existing issues)

---

## Quick Reference

### Baseline Checklist

**Before starting work**:
- [ ] Run full test suite
- [ ] Document results (passed/failed/skipped)
- [ ] Note any existing failures
- [ ] Record coverage baseline
- [ ] Commit baseline documentation

**During development**:
- [ ] Add new tests for new features
- [ ] Run tests frequently
- [ ] Compare to baseline
- [ ] Investigate new failures immediately

**Before merging**:
- [ ] All tests pass (or failures documented/tracked)
- [ ] Baseline maintained or improved
- [ ] No regressions introduced
- [ ] Coverage maintained or increased

---

## Key Takeaways

**Remember**:
- 🔍 **Baseline before changes** (know your starting point)
- 🔍 **Document failures** (don't hide pre-existing issues)
- 🔍 **Separate concerns** (your work vs legacy)
- 🔍 **Track per-platform** (different baselines OK)
- 🔍 **Fix flaky tests** (high priority)
- 🔍 **Update baseline** (when fixing legacy issues)

**Philosophy**:
> "Know your starting point before making changes. Establishing a baseline makes it crystal clear what your code affected, enabling faster debugging and preventing blame for pre-existing issues."

---

**Related**:
- [TDD Principles](tdd-principles.md) - Write tests first
- [Testing Requirements](../standards/testing-requirements.md) - Test standards
- [Development Workflow](../processes/development-workflow.md) - Baseline in workflow
- [Independent Verification](independent-verification.md) - Cross-platform baselines
