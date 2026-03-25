# Test-Driven Development (TDD) Principles

> **Core Principle #2**: Write tests first, then write code to make the tests pass.

---

## The TDD Philosophy

**Workflow**: Write tests first, then write code to make the tests pass.

> **Critical**: Make the **CODE** pass the **TEST**, not the other way around.  
> Tests define correct behavior; code implements that behavior.

**When to modify tests**:
- ✅ Improve test quality or clarity
- ✅ Split tests when discovering new edge cases
- ✅ Refine tests when requirements become clearer
- ❌ **Never** change tests just to make broken code pass

---

## The TDD Cycle

###

 Standard TDD Cycle

```
1. Write failing test (RED)
   ↓
2. Write code to pass test (GREEN)
   ↓
3. Refactor code and tests (REFACTOR)
   ↓
4. Repeat
```

### Detailed Steps

**RED Phase**:
```python
def test_upload_attachment_creates_new_version():
    """Test that upload creates new version when file exists."""
    # Arrange
    existing_attachment = create_attachment("test.png")
    
    # Act
    result = upload_attachment("test.png", data)
    
    # Assert
    assert result.version == 2  # ← TEST FAILS (not implemented)
```

**GREEN Phase**:
```python
def upload_attachment(filename, data):
    """Upload attachment, creating new version if exists."""
    existing = get_attachment_by_name(filename)
    if existing:
        return create_new_version(existing, data)  # ← Code to pass test
    return create_attachment(filename, data)
```

**REFACTOR Phase**:
```python
# Improve code quality without changing behavior
def upload_attachment(filename, data):
    """Upload attachment, creating new version if exists."""
    if existing_attachment := get_attachment_by_name(filename):
        return existing_attachment.create_version(data)
    return Attachment.create(filename, data)
```

---

## Extended TDD Cycle (with UAT)

```
Phase 1: Unit Tests (TDD)
├─ Write unit tests for new feature
├─ Implement feature to pass tests
└─ Refactor for quality

Phase 2: Integration Tests
├─ Write integration tests
├─ Fix integration issues
└─ Verify end-to-end flow

Phase 3: UAT (User Acceptance Testing)
├─ Test in real environment
├─ Discover edge cases
├─ Fix and re-test
└─ Document learnings

Phase 4: Cross-Platform Validation
├─ Test on all target platforms
├─ Fix platform-specific issues
└─ Verify universal compatibility
```

---

## Why TDD?

### Benefits

**Design Benefits**:
- ✅ Forces you to think about API before implementation
- ✅ Results in more testable, modular code
- ✅ Clarifies requirements (tests are executable specs)

**Quality Benefits**:
- ✅ High test coverage by default (100% for new code)
- ✅ Catches bugs immediately (fast feedback)
- ✅ Regression protection (tests prevent breakage)
- ✅ Confidence to refactor (tests verify behavior preserved)

**Productivity Benefits**:
- ✅ Less debugging time (tests pinpoint issues)
- ✅ Faster development (clear goal: make test pass)
- ✅ Better documentation (tests show usage)
- ✅ Easier maintenance (tests document intent)

### The Cost of NOT Using TDD

**Without TDD**:
```
Write code → Manual testing → Bug found → Debug → Fix → Re-test
→ More bugs found → Repeat cycle → Technical debt accumulates
→ Fear of refactoring → Code quality degrades
```

**Time wasted**:
- Manual testing: Repetitive, error-prone
- Debugging: Hard to isolate issues
- Regression bugs: Breaking existing features
- Refactoring fear: "If it works, don't touch it"

**With TDD**:
```
Write test → Write code → Test passes → Refactor with confidence
→ High coverage → Fast feedback → Quality improves
→ Safe refactoring → Sustainable velocity
```

---

## TDD Best Practices

### Test Structure (Arrange-Act-Assert)

```python
def test_feature_does_something_when_condition():
    """Test that feature does X when Y occurs."""
    # Arrange - Set up test data and state
    user = create_user("test@example.com")
    attachment = create_attachment("test.png")
    
    # Act - Execute the behavior being tested
    result = user.download_attachment(attachment)
    
    # Assert - Verify expected outcome
    assert result.success == True
    assert result.file_path.exists()
```

### Test Naming Convention

```python
# Pattern: test_<function>_<scenario>_<expected_result>

def test_upload_attachment_creates_new_version_when_file_exists():
    """Test that upload creates new version when file already exists."""
    pass

def test_upload_attachment_raises_error_when_size_exceeds_limit():
    """Test that upload raises error when file size exceeds limit."""
    pass

def test_download_attachment_returns_file_path_when_successful():
    """Test that download returns file path when successful."""
    pass
```

### One Assert Per Test (Guideline)

**Prefer**:
```python
def test_upload_returns_success():
    result = upload_attachment("test.png", data)
    assert result.success == True

def test_upload_returns_attachment_id():
    result = upload_attachment("test.png", data)
    assert result.attachment_id is not None

def test_upload_increments_version():
    result = upload_attachment("test.png", data)
    assert result.version == 2
```

**Over** (harder to debug when fails):
```python
def test_upload_attachment():
    result = upload_attachment("test.png", data)
    assert result.success == True
    assert result.attachment_id is not None
    assert result.version == 2
    # Which assertion failed?
```

**Exception**: Related assertions OK:
```python
def test_upload_returns_valid_result():
    result = upload_attachment("test.png", data)
    assert result.success == True
    assert result.attachment_id is not None  # Related to success
```

### Test Independence

**Each test should**:
- ✅ Set up its own data (Arrange phase)
- ✅ Run independently of other tests
- ✅ Clean up after itself (or use fixtures)
- ✅ Not depend on test execution order

```python
# ✅ Good - Independent
def test_delete_attachment():
    attachment = create_attachment("test.png")  # Own setup
    result = delete_attachment(attachment.id)
    assert result.success == True

# ❌ Bad - Depends on previous test
def test_delete_attachment():
    # Assumes attachment from previous test exists
    result = delete_attachment("some-id")
    assert result.success == True
```

---

## TDD with Mocks

### When to Mock

**Mock external dependencies**:
- ✅ API calls (Confluence, Jira)
- ✅ Database queries
- ✅ File system operations (sometimes)
- ✅ Network requests
- ✅ Time/date (for deterministic tests)

**Don't mock**:
- ❌ Code you own (test actual implementation)
- ❌ Simple data structures
- ❌ Pure functions

### Mock Example

```python
from unittest.mock import Mock, patch

def test_upload_calls_api_with_correct_params():
    """Test that upload calls Confluence API with correct parameters."""
    # Arrange
    mock_api = Mock()
    mock_api.upload.return_value = {"id": "123", "version": 2}
    
    # Act
    with patch('confluence.api', mock_api):
        result = upload_attachment("test.png", b"data")
    
    # Assert
    mock_api.upload.assert_called_once_with(
        filename="test.png",
        data=b"data",
        content_type="image/png"
    )
    assert result["version"] == 2
```

---

## Coverage Targets

### New Code

**Target**: **100% coverage** for all new code

- Every function has tests
- Every branch (if/else) has tests
- Every exception path has tests
- Every edge case has tests

### Existing Code

**When modifying**:
- Test new behavior: 100%
- Test modified behavior: 100%
- Test adjacent code: As feasible

**When refactoring**:
- Existing tests must pass
- Add tests for uncovered areas
- Aim for 100% of refactored code

---

## Common TDD Anti-Patterns

### Anti-Pattern 1: Writing Tests After Code

```
❌ Write code → "I should add tests" → Write tests to match code
✅ Write test → Code fails → Write code to pass test
```

**Why it matters**: Tests written after code tend to just verify what code does, not what it should do.

### Anti-Pattern 2: Changing Tests to Pass Code

```
❌ Test fails → Modify test to pass → Test passes (but code is wrong)
✅ Test fails → Fix code to pass test → Test passes (code is correct)
```

**Remember**: Tests define correct behavior. Change code, not tests.

### Anti-Pattern 3: Testing Implementation, Not Behavior

```python
# ❌ Bad - Tests implementation details
def test_upload_uses_put_method():
    assert upload_code.uses_http_method("PUT")

# ✅ Good - Tests behavior
def test_upload_creates_new_version_when_file_exists():
    result = upload_attachment("existing.png", data)
    assert result.version == 2
```

### Anti-Pattern 4: Giant Test Methods

```python
# ❌ Bad - Tests everything in one method
def test_attachment_operations():
    # Upload test
    result = upload()
    assert result.success
    
    # Download test
    file = download()
    assert file.exists
    
    # Delete test
    deleted = delete()
    assert deleted
    # Hard to debug when fails!

# ✅ Good - Focused tests
def test_upload_succeeds():
    result = upload()
    assert result.success

def test_download_returns_file():
    file = download()
    assert file.exists

def test_delete_succeeds():
    result = delete()
    assert result == True
```

---

## TDD with Legacy Code

### Adding Tests to Untested Code

**Strategy**:
1. Identify area to modify
2. Write **characterization tests** (document current behavior)
3. Refactor for testability (extract dependencies)
4. Write tests for new behavior
5. Implement new feature with TDD

**Characterization Test Example**:
```python
def test_current_behavior_of_legacy_function():
    """Document what the code currently does (even if wrong)."""
    result = legacy_function(input_data)
    assert result == current_output  # What it does now, not what it should do
```

---

## Quick Reference

### TDD Checklist

**Before implementing a feature**:
- [ ] Write failing test for desired behavior
- [ ] Verify test fails for right reason (RED)
- [ ] Write minimal code to make test pass (GREEN)
- [ ] Verify test passes
- [ ] Refactor code and tests (REFACTOR)
- [ ] Repeat for next behavior

**When test fails**:
- [ ] Understand why it fails
- [ ] Fix **code** to pass test (not test to pass code)
- [ ] Verify fix resolves failure
- [ ] Check for related edge cases

**When refactoring**:
- [ ] All tests still pass
- [ ] Behavior unchanged (tests verify)
- [ ] Code quality improved
- [ ] Coverage maintained or improved

---

## Key Takeaways

**Remember**:
- ✅ **Tests first, code second** (TDD)
- ✅ **Change code to pass tests** (not tests to pass code)
- ✅ **RED → GREEN → REFACTOR** (the cycle)
- ✅ **100% coverage for new code** (target)
- ✅ **Independent tests** (no ordering dependencies)
- ✅ **One concept per test** (easy debugging)

**TDD Philosophy**:
> "Tests define correct behavior. Code implements that behavior. When tests fail, we fix the code. When requirements change, we update tests first, then code."

---

**Related**:
- [Baseline-First Testing](baseline-first-testing.md) - Know your starting point
- [Testing Requirements](../standards/testing-requirements.md) - Detailed test standards
- [Development Workflow](../processes/development-workflow.md) - TDD in practice
- [Code Quality Standards](../standards/code-quality-standards.md) - Quality expectations
