# Testing Requirements

> **Testing is non-negotiable**: Comprehensive tests ensure reliability and prevent regressions.

---

## Overview

Testing requirements define what tests are needed, when, and at what quality level:

- **Coverage**: How much code must be tested
- **Test types**: Unit, integration, UAT
- **Test quality**: What makes a good test
- **When to test**: Throughout development (TDD)

---

## Coverage Requirements

### Minimum Coverage Targets

**New code**:
- ✅ **≥ 80% coverage** (unit + integration combined)
- ✅ **100% for critical paths** (auth, security, payment, data loss)
- ✅ **100% for bug fixes** (regression tests mandatory)

**Legacy code** (already exists):
- ⚠️ **No coverage requirement** (don't make worse)
- ✅ **Add tests if modifying** (test your changes)
- ✅ **Document untested areas** (tech debt)

### Measure Coverage

**Python**:
```bash
# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Fail if below threshold
pytest --cov=src --cov-fail-under=80
```

**JavaScript**:
```bash
# Run with coverage
npm test -- --coverage

# View HTML report
open coverage/index.html
```

**Go**:
```bash
# Run with coverage
go test -cover ./...

# Detailed HTML report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Coverage is Not Everything

**High coverage ≠ well-tested**:
- 100% coverage with bad tests = false confidence
- 80% coverage with great tests > 100% coverage with poor tests
- Test quality matters more than quantity

**What coverage doesn't measure**:
- Edge cases tested
- Error paths validated
- Integration scenarios covered
- Real-world usage verified

---

## Test Types Required

### 1. Unit Tests

**Purpose**: Test individual functions/classes in isolation.

**Characteristics**:
- ✅ **Fast** (< 1 second per test)
- ✅ **Isolated** (no external dependencies)
- ✅ **Deterministic** (same input → same output)
- ✅ **Focused** (test one thing)

**Example**:
```python
def test_calculate_discount():
    """Test discount calculation with valid inputs."""
    result = calculate_discount(price=100, rate=0.2)
    assert result == 80

def test_calculate_discount_zero():
    """Test discount with zero rate."""
    result = calculate_discount(price=100, rate=0.0)
    assert result == 100

def test_calculate_discount_invalid():
    """Test discount with invalid rate."""
    with pytest.raises(ValueError):
        calculate_discount(price=100, rate=1.5)
```

**When required**:
- ✅ **Always** (for all new functions/methods)
- ✅ **Before implementation** (TDD approach)
- ✅ **After bug fixes** (regression tests)

---

### 2. Integration Tests

**Purpose**: Test interaction between multiple components.

**Characteristics**:
- ✅ **Moderate speed** (1-10 seconds per test)
- ✅ **Real dependencies** (or realistic mocks)
- ✅ **Realistic scenarios** (how components work together)
- ✅ **Broader scope** (multiple units)

**Example**:
```python
def test_upload_attachment_integration():
    """Test attachment upload with real API client."""
    client = ConfluenceClient(base_url, api_key)
    fetcher = ConfluenceFetcher(client)
    
    result = fetcher.upload_attachment(
        page_id="123456",
        filepath="test.pdf"
    )
    
    assert result["success"] is True
    assert "attachment_id" in result
```

**When required**:
- ✅ **For features with dependencies** (API calls, databases)
- ✅ **After unit tests pass** (integration is next step)
- ✅ **Before UAT** (verify components work together)

**Mocking vs Real Dependencies**:
- **Mock**: Fast, predictable, no external setup
- **Real**: Realistic, catches integration issues, slower
- **Balance**: Mock for unit tests, use real for integration tests

---

### 3. UAT (User Acceptance Testing)

**Purpose**: Verify features work in real-world scenarios.

**Characteristics**:
- ✅ **Manual execution** (not automated)
- ✅ **Realistic data** (production-like scenarios)
- ✅ **User workflows** (end-to-end scenarios)
- ✅ **Cross-platform** (test on all target platforms)

**Example**:
```markdown
## UAT Scenario: Upload Attachment

**Steps**:
1. Log into Confluence test instance
2. Create test page
3. Upload 3 files (PDF, PNG, XLSX)
4. Verify all files appear in Confluence UI
5. Download files and verify integrity

**Expected**: All 3 files uploaded and downloadable
**Actual**: ✅ All 3 files working
**Status**: PASSED
```

**When required**:
- ✅ **Before merging** (Phase 6 of workflow)
- ✅ **For user-facing features** (APIs, UI)
- ✅ **After bug fixes** (verify fix in real environment)
- ✅ **Cross-platform code** (test on Windows, Linux, macOS)

(See [UAT Testing Guide](../processes/uat-testing-guide.md) for detailed templates)

---

## Test Quality Standards

### Good Test Characteristics

**FIRST Principles**:
- **F**ast: Run quickly (< 1 second per unit test)
- **I**solated: Independent of other tests
- **R**epeatable: Same result every time
- **S**elf-validating: Pass/fail, no manual inspection
- **T**imely: Written with code (TDD)

### What Makes a Good Test

**✅ Good test**:
```python
def test_upload_attachment_success():
    """Test successful attachment upload returns attachment ID."""
    # Arrange
    mock_client = Mock()
    mock_client.attach_file.return_value = {
        "id": "att123",
        "title": "test.pdf",
        "size": 1234
    }
    mixin = AttachmentsMixin(mock_client)
    
    # Act
    result = mixin.upload_attachment(page_id="123", filepath="test.pdf")
    
    # Assert
    assert result["success"] is True
    assert result["attachment_id"] == "att123"
    mock_client.attach_file.assert_called_once()
```

**Why it's good**:
- ✅ **Clear name**: Describes what is tested
- ✅ **Arrange-Act-Assert**: Clear structure
- ✅ **One assertion focus**: Tests one thing
- ✅ **Isolated**: Uses mocks, no external dependencies
- ✅ **Fast**: Executes in milliseconds

**❌ Bad test**:
```python
def test_stuff():
    """Test some stuff."""
    # No clear arrange/act/assert
    client = Client()
    result = client.do_things()
    # Depends on real API, slow, flaky
    assert result  # What does this test?
```

**Why it's bad**:
- ❌ **Vague name**: "stuff" doesn't describe what is tested
- ❌ **No structure**: Hard to understand
- ❌ **Real dependencies**: Slow, requires external services
- ❌ **Unclear assertion**: What behavior is validated?

---

## Test Patterns

### Arrange-Act-Assert (AAA)

**Structure all tests with AAA**:
```python
def test_example():
    # Arrange: Set up test data and mocks
    user = User(name="Alice", age=30)
    
    # Act: Execute the code being tested
    result = user.is_adult()
    
    # Assert: Verify the result
    assert result is True
```

### Parameterized Tests

**Test multiple inputs efficiently**:
```python
@pytest.mark.parametrize("price,discount,expected", [
    (100, 0.1, 90),     # 10% discount
    (100, 0.0, 100),    # No discount
    (100, 0.5, 50),     # 50% discount
    (100, 1.0, 0),      # 100% discount (free)
])
def test_calculate_discount(price, discount, expected):
    result = calculate_discount(price, discount)
    assert result == expected
```

### Fixtures for Setup

**Reuse common setup**:
```python
@pytest.fixture
def confluence_client():
    """Fixture providing configured Confluence client."""
    return ConfluenceClient(
        base_url="https://test.atlassian.net",
        api_key="test-key"
    )

def test_upload(confluence_client):
    # Use fixture
    result = confluence_client.upload_file("test.pdf")
    assert result["success"]
```

### Mocking External Dependencies

**Mock APIs, databases, file systems**:
```python
from unittest.mock import Mock, patch

def test_upload_calls_api():
    """Test that upload makes correct API call."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"id": "123"}
        
        uploader = FileUploader()
        result = uploader.upload("test.pdf")
        
        # Verify API called correctly
        mock_post.assert_called_once()
        assert result["id"] == "123"
```

---

## Test Coverage Best Practices

### What to Test

**✅ Always test**:
- Public APIs (all functions/methods exposed to users)
- Critical paths (auth, security, payment, data loss)
- Error handling (all exception paths)
- Edge cases (boundary conditions, empty inputs)
- Bug fixes (regression tests prevent re-occurrence)

**⚠️ Consider testing**:
- Internal helper functions (if complex logic)
- Configuration parsing (if non-trivial)
- Data transformations (input → output)

**❌ Don't test**:
- Third-party libraries (trust they're tested)
- Trivial getters/setters (unless they have logic)
- Auto-generated code (unless you wrote the generator)

### Coverage Gaps Are OK

**Acceptable gaps**:
- Platform-specific code (if tested on that platform)
- Defensive error handling (hard to trigger)
- Legacy code (if not modifying)

**Unacceptable gaps**:
- New feature code (must test)
- Bug fix code (must have regression test)
- Critical paths (auth, security, etc.)

---

## Regression Tests

### What is a Regression Test?

**Definition**: Test that prevents a fixed bug from reoccurring.

**Purpose**: Ensure bug stays fixed through future changes.

### When Required

**✅ Always write regression tests for**:
- Every bug fix (no exceptions)
- Security vulnerabilities fixed
- Data corruption issues fixed
- Production incidents resolved

### Example Regression Test

**Bug**: Upload fails for files > 100MB due to timeout.

**Fix**: Increased timeout from 30s to 120s.

**Regression test**:
```python
def test_upload_large_file_does_not_timeout():
    """Regression test for issue #42: Large file upload timeout.
    
    Bug: Files > 100MB failed with timeout after 30 seconds.
    Fix: Increased timeout to 120 seconds.
    """
    mock_client = Mock()
    mock_client.attach_file.return_value = {"id": "att123"}
    
    mixin = AttachmentsMixin(mock_client)
    
    # Simulate large file (would take >30s before fix)
    result = mixin.upload_attachment(
        page_id="123",
        filepath="large_file_150mb.pdf"
    )
    
    # Should succeed now (not timeout)
    assert result["success"] is True
    
    # Verify timeout parameter passed correctly
    call_args = mock_client.attach_file.call_args
    assert call_args.kwargs.get("timeout", 30) == 120
```

---

## Test Organization

### Directory Structure

**Mirror source structure**:
```
project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── uploader.py
│       └── downloader.py
├── tests/
│   ├── unit/
│   │   ├── test_uploader.py
│   │   └── test_downloader.py
│   └── integration/
│       └── test_upload_flow.py
```

### Test File Naming

**Convention**:
- `test_*.py` or `*_test.py` (Python)
- `*.test.js` or `*.spec.js` (JavaScript)
- `*_test.go` (Go)

**Match source files**:
- `uploader.py` → `test_uploader.py`
- `api_client.js` → `api_client.test.js`

---

## Running Tests

### Run All Tests

```bash
# Python
pytest

# JavaScript
npm test

# Go
go test ./...
```

### Run Specific Tests

```bash
# Python: Single file
pytest tests/unit/test_uploader.py

# Python: Single test function
pytest tests/unit/test_uploader.py::test_upload_success

# JavaScript: Single file
npm test -- api_client.test.js

# Go: Single package
go test ./pkg/uploader
```

### Run with Coverage

```bash
# Python
pytest --cov=src --cov-report=html

# JavaScript
npm test -- --coverage

# Go
go test -cover ./...
```

---

## Quick Reference Checklist

### Before Committing

**Test execution**:
- [ ] All tests pass (100% pass rate)
- [ ] No skipped tests (unless intentional)
- [ ] Coverage ≥ 80% for new code
- [ ] Regression tests for bug fixes

**Test quality**:
- [ ] Tests follow AAA pattern
- [ ] Clear test names (describe what is tested)
- [ ] Isolated (no external dependencies for unit tests)
- [ ] Fast (unit tests < 1 second each)

**Coverage**:
- [ ] Public APIs tested
- [ ] Error paths tested
- [ ] Edge cases tested
- [ ] Critical paths 100% covered

---

## Key Takeaways

**Remember**:
- 🧪 **Tests are mandatory** (not optional)
- 🧪 **Write tests first** (TDD approach)
- 🧪 **Quality over quantity** (good tests matter)
- 🧪 **Regression tests always** (for every bug fix)
- 🧪 **Coverage ≥ 80%** (for new code)

**Philosophy**:
> "Tests are not extra work—they're the foundation of reliable software. Write them first, make them good, and maintain them forever."

**Culture**:
> "Code without tests is legacy code. Every feature, every bug fix, every change deserves comprehensive tests."

---

**Related**:
- [TDD Principles](../philosophy/tdd-principles.md) - Test-driven development approach
- [Code Quality Standards](code-quality-standards.md) - Testing standards
- [UAT Testing Guide](../processes/uat-testing-guide.md) - User acceptance testing
- [Development Workflow](../processes/development-workflow.md) - Testing in workflow
