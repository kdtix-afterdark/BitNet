# Code Quality Standards

> **Quality is not negotiable**: Standards ensure consistency, maintainability, and reliability.

---

## Overview

Code quality standards define the minimum acceptable quality for all code:

- **Testing**: Coverage, test types, test quality
- **Style**: Formatting, naming, documentation
- **Type Safety**: Type hints, type checking
- **Maintainability**: Complexity, duplication, clarity

---

## Testing Standards

### Coverage Requirements

**Minimum coverage**:
- ✅ **New code**: ≥ 80% coverage (unit + integration)
- ✅ **Critical paths**: 100% coverage (auth, security, data loss scenarios)
- ✅ **Bug fixes**: 100% coverage (regression tests required)

**Measure coverage**:
```bash
# Python
pytest --cov=src --cov-report=html --cov-report=term

# JavaScript
npm test -- --coverage

# Go
go test -cover ./...
```

**Coverage is not everything**:
- 100% coverage ≠ well-tested
- Test quality matters more than quantity
- Cover critical paths, edge cases, error handling

### Test Types Required

**1. Unit Tests** (isolation testing):
```python
def test_calculate_discount():
    # Test single function in isolation
    result = calculate_discount(price=100, discount=0.2)
    assert result == 80
```

**2. Integration Tests** (component interaction):
```python
def test_user_registration_flow():
    # Test multiple components together
    user = register_user(email="test@example.com", password="pass123")
    assert user.is_active
    assert send_welcome_email_called(user.email)
```

**3. Edge Case Tests** (boundary conditions):
```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_empty_list():
    result = calculate_average([])
    assert result == 0  # Or raises ValueError
```

**4. Error Handling Tests** (failure scenarios):
```python
def test_api_timeout():
    with pytest.raises(TimeoutError):
        fetch_data(timeout=0.001)

def test_invalid_input():
    with pytest.raises(ValueError):
        validate_email("not-an-email")
```

### Test Quality Standards

**✅ Good tests**:
- **Isolated**: No dependencies on other tests
- **Deterministic**: Same input → same output (no flaky tests)
- **Fast**: Run quickly (< 1 second per test ideally)
- **Clear**: Obvious what is being tested
- **Focused**: Test one thing per test

**❌ Bad tests**:
- **Coupled**: Depend on execution order
- **Flaky**: Pass/fail randomly
- **Slow**: Take minutes to run
- **Unclear**: Hard to understand what failed
- **Overly broad**: Test too many things at once

**Example comparison**:

**❌ Bad test**:
```python
def test_everything():
    # Tests too many things at once
    user = create_user()
    user.update_profile()
    user.add_payment_method()
    user.purchase_item()
    assert user.balance == 0
    # If this fails, what broke?
```

**✅ Good test**:
```python
def test_create_user_sets_default_balance():
    user = create_user()
    assert user.balance == 0

def test_purchase_item_deducts_balance():
    user = create_user(balance=100)
    user.purchase_item(price=30)
    assert user.balance == 70
```

---

## Code Style Standards

### Formatting

**Python**:
- **Line length**: 88 characters (Black/Ruff default)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings (configurable)
- **Imports**: Sorted alphabetically, grouped (stdlib, third-party, local)

```python
# ✅ Good formatting
def calculate_total(
    items: list[Item],
    tax_rate: float = 0.08,
    discount: float = 0.0,
) -> float:
    """Calculate order total with tax and discount."""
    subtotal = sum(item.price for item in items)
    discounted = subtotal * (1 - discount)
    return discounted * (1 + tax_rate)
```

**JavaScript/TypeScript**:
- **Line length**: 80-100 characters
- **Indentation**: 2 spaces
- **Semicolons**: Required (or consistently omitted)
- **Trailing commas**: Yes (for multi-line)

```typescript
// ✅ Good formatting
function calculateTotal(
  items: Item[],
  taxRate: number = 0.08,
  discount: number = 0.0
): number {
  const subtotal = items.reduce((sum, item) => sum + item.price, 0);
  const discounted = subtotal * (1 - discount);
  return discounted * (1 + taxRate);
}
```

### Naming Conventions

**Python**:
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

```python
# ✅ Good naming
MAX_RETRY_COUNT = 3

class UserAccount:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self._cached_balance = None
    
    def get_balance(self) -> float:
        if self._cached_balance is None:
            self._cached_balance = self._fetch_balance()
        return self._cached_balance
```

**JavaScript/TypeScript**:
- **Functions/variables**: `camelCase`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `#privateField` or `_leadingUnderscore`

```typescript
// ✅ Good naming
const MAX_RETRY_COUNT = 3;

class UserAccount {
  private accountId: string;
  private cachedBalance?: number;
  
  constructor(accountId: string) {
    this.accountId = accountId;
  }
  
  getBalance(): number {
    if (this.cachedBalance === undefined) {
      this.cachedBalance = this.fetchBalance();
    }
    return this.cachedBalance;
  }
}
```

### Documentation Standards

**All public APIs must have docstrings**:

**Python (Google-style)**:
```python
def upload_file(
    filepath: str,
    timeout: int = 30,
    retry: bool = True,
) -> dict[str, Any]:
    """Upload a file to the server.
    
    Uploads the specified file with configurable timeout and retry behavior.
    Returns upload metadata including file ID and size.
    
    Args:
        filepath: Path to file to upload (absolute or relative)
        timeout: Request timeout in seconds (default: 30)
        retry: Whether to retry on transient failures (default: True)
    
    Returns:
        Dictionary containing:
            - success (bool): Whether upload succeeded
            - file_id (str): Unique identifier for uploaded file
            - size (int): File size in bytes
            - error (str, optional): Error message if success is False
    
    Raises:
        FileNotFoundError: If filepath doesn't exist
        TimeoutError: If upload exceeds timeout and retry is False
        PermissionError: If user lacks permissions
    
    Example:
        >>> result = upload_file("document.pdf", timeout=60)
        >>> print(result["file_id"])
        "abc123"
    """
```

**TypeScript (JSDoc)**:
```typescript
/**
 * Upload a file to the server.
 * 
 * Uploads the specified file with configurable timeout and retry behavior.
 * Returns upload metadata including file ID and size.
 * 
 * @param filepath - Path to file to upload (absolute or relative)
 * @param timeout - Request timeout in seconds (default: 30)
 * @param retry - Whether to retry on transient failures (default: true)
 * @returns Upload result with file ID and metadata
 * @throws {FileNotFoundError} If filepath doesn't exist
 * @throws {TimeoutError} If upload exceeds timeout
 * 
 * @example
 * const result = await uploadFile("document.pdf", 60);
 * console.log(result.fileId);
 */
async function uploadFile(
  filepath: string,
  timeout: number = 30,
  retry: boolean = true
): Promise<UploadResult> {
  // Implementation
}
```

---

## Type Safety Standards

### Type Hints Required

**Python** (type hints on all functions):
```python
# ❌ No type hints
def process_data(data, config):
    return data.transform(config)

# ✅ With type hints
def process_data(data: DataFrame, config: dict[str, Any]) -> DataFrame:
    return data.transform(config)
```

**Modern union syntax**:
```python
# ❌ Old style
from typing import Optional, Union
def get_user(user_id: str) -> Optional[User]:
    pass

# ✅ Modern style (Python 3.10+)
def get_user(user_id: str) -> User | None:
    pass

def parse_value(value: str | int | float) -> float:
    pass
```

### Type Checking Required

**Python**:
```bash
# Must pass mypy or pyright
mypy src/
pyright src/
```

**TypeScript**:
```bash
# Must pass tsc
tsc --noEmit
```

**Type strictness**:
```python
# pyproject.toml or mypy.ini
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true
  }
}
```

---

## Maintainability Standards

### Complexity Limits

**Function complexity** (cyclomatic complexity):
- ✅ **Simple**: < 10 (ideal)
- ⚠️ **Moderate**: 10-20 (consider refactoring)
- ❌ **Complex**: > 20 (must refactor)

**Function length**:
- ✅ **Short**: < 50 lines (ideal)
- ⚠️ **Medium**: 50-100 lines (consider splitting)
- ❌ **Long**: > 100 lines (must split)

**Example refactoring**:

**❌ Too complex** (cyclomatic complexity = 15):
```python
def process_order(order: Order) -> dict[str, Any]:
    if order.status == "pending":
        if order.payment_method == "credit_card":
            if order.total > 1000:
                if order.customer.credit_score > 700:
                    # Process high-value order
                else:
                    # Reject low credit
            else:
                # Process normal order
        elif order.payment_method == "paypal":
            # Process PayPal order
        else:
            # Unknown payment method
    else:
        # Order not pending
    # More branches...
```

**✅ Refactored** (complexity reduced):
```python
def process_order(order: Order) -> dict[str, Any]:
    if order.status != "pending":
        return {"error": "Order not pending"}
    
    validator = PaymentValidator(order)
    if not validator.is_valid():
        return {"error": validator.error_message}
    
    processor = PaymentProcessor.for_method(order.payment_method)
    return processor.process(order)
```

### Code Duplication

**DRY principle** (Don't Repeat Yourself):

**❌ Duplicated**:
```python
def calculate_discount_customer_a(total):
    if total > 1000:
        return total * 0.9
    return total

def calculate_discount_customer_b(total):
    if total > 1000:
        return total * 0.9
    return total
```

**✅ Refactored**:
```python
def calculate_discount(total: float, threshold: float = 1000, rate: float = 0.1) -> float:
    if total > threshold:
        return total * (1 - rate)
    return total
```

### Clarity Standards

**✅ Self-documenting code**:
```python
# ✅ Clear variable names
user_registration_date = user.created_at
days_since_registration = (datetime.now() - user_registration_date).days

# ❌ Unclear names
d = user.created_at
x = (datetime.now() - d).days
```

**✅ Avoid magic numbers**:
```python
# ❌ Magic number
if user.age > 18:
    grant_access()

# ✅ Named constant
MINIMUM_AGE = 18
if user.age >= MINIMUM_AGE:
    grant_access()
```

**✅ Extract complex conditions**:
```python
# ❌ Complex inline condition
if user.is_active and user.subscription.is_paid and not user.is_banned and user.email_verified:
    grant_premium_access()

# ✅ Named function
def is_eligible_for_premium(user: User) -> bool:
    return (
        user.is_active
        and user.subscription.is_paid
        and not user.is_banned
        and user.email_verified
    )

if is_eligible_for_premium(user):
    grant_premium_access()
```

---

## Error Handling Standards

### Use Specific Exceptions

**❌ Generic exceptions**:
```python
try:
    result = process_data(data)
except Exception:  # Too broad!
    return {"error": "Something went wrong"}
```

**✅ Specific exceptions**:
```python
try:
    result = process_data(data)
except ValueError as e:
    return {"error": f"Invalid data: {e}"}
except FileNotFoundError as e:
    return {"error": f"File not found: {e}"}
except PermissionError as e:
    return {"error": f"Permission denied: {e}"}
```

### Never Silent Failures

**❌ Silent failure**:
```python
try:
    upload_file(filepath)
except Exception:
    pass  # Error swallowed!
```

**✅ Log and handle**:
```python
try:
    upload_file(filepath)
except Exception as e:
    logger.error(f"Upload failed: {e}")
    raise  # Re-raise or return error
```

---

## Quick Reference Checklist

### Before Committing

**Testing**:
- [ ] All tests pass (`pytest`, `npm test`)
- [ ] New code has ≥ 80% coverage
- [ ] Bug fixes have regression tests
- [ ] Edge cases tested

**Style**:
- [ ] Code formatted (`ruff format`, `prettier`)
- [ ] Linter passes (`ruff check`, `eslint`)
- [ ] Naming conventions followed
- [ ] No debug code (`print()`, `console.log()`)

**Type Safety**:
- [ ] Type hints on all functions
- [ ] Type checker passes (`mypy`, `tsc`)
- [ ] Modern syntax used (e.g., `str | None`)

**Documentation**:
- [ ] Public APIs have docstrings
- [ ] Complex logic has comments
- [ ] Examples provided for new features

**Maintainability**:
- [ ] Functions < 50 lines
- [ ] Complexity < 10 (ideally)
- [ ] No code duplication
- [ ] Clear variable names

---

## Enforcement

### Pre-Commit Hooks

**Automatically enforce standards**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff-format  # Formatting
      - id: ruff         # Linting
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy         # Type checking
```

**Install hooks**:
```bash
pre-commit install
```

### CI/CD Pipeline

**GitHub Actions example**:
```yaml
name: Quality Checks
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src --cov-fail-under=80
      - run: ruff check
      - run: ruff format --check
      - run: mypy src/
```

---

## Key Takeaways

**Remember**:
- 📏 **Standards are minimum** (not aspirational)
- 📏 **Automate enforcement** (pre-commit hooks, CI/CD)
- 📏 **Quality over quantity** (tests, docs, code)
- 📏 **Consistency matters** (style, naming, patterns)
- 📏 **Refactor complexity** (keep functions simple)

**Philosophy**:
> "Code quality standards aren't bureaucracy—they're the foundation for maintainable, reliable software. Enforce them automatically and consistently."

**Culture**:
> "Quality is everyone's responsibility. Pre-commit hooks and CI/CD ensure no code bypasses standards."

---

**Related**:
- [Testing Requirements](testing-requirements.md) - Detailed test standards
- [Pre-Commit Verification](pre-commit-verification.md) - Quality gates
- [TDD Principles](../philosophy/tdd-principles.md) - Test-driven approach
- [Development Workflow](../processes/development-workflow.md) - Quality in workflow
