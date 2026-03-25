# Pre-Commit Verification

> **Final Quality Gate**: Ensure all standards met before committing code.

---

## Overview

Pre-commit verification is the **final quality gate** before code enters version control:

- Catches issues before they reach CI/CD
- Enforces standards automatically
- Prevents broken commits
- Saves time (faster feedback than CI/CD)

**Philosophy**: If it doesn't pass pre-commit, it doesn't get committed.

---

## Pre-Commit Checklist

### 1. All Tests Pass ✅

**Run full test suite**:
```bash
# Python
pytest -v

# JavaScript
npm test

# Go
go test ./...
```

**Expected**:
- ✅ **All tests pass** (100% pass rate)
- ✅ **No skipped tests** (unless by design)
- ✅ **Fast execution** (< 30 seconds ideally)

**If tests fail**:
- ❌ **Do NOT commit**
- ❌ **Do NOT use `--no-verify` to bypass**
- ✅ **Fix failing tests first**
- ✅ **Investigate why they failed**

---

### 2. Code Formatting ✅

**Run formatter**:
```bash
# Python
ruff format .

# JavaScript
prettier --write .

# Go
gofmt -w .
```

**Check formatting** (dry run):
```bash
# Python
ruff format --check .

# JavaScript
prettier --check .
```

**Expected**:
- ✅ **No changes needed** (all files formatted)
- ✅ **Consistent style** (88 chars for Python, etc.)

---

### 3. Linting ✅

**Run linter**:
```bash
# Python
ruff check .

# JavaScript
eslint src/

# Go
golint ./...
```

**Expected**:
- ✅ **Zero warnings** (clean lint)
- ✅ **Zero errors** (no violations)

**Common linting issues**:
- Unused imports
- Unused variables
- Missing type hints
- Complexity too high
- Line too long

**Fix automatically** (where possible):
```bash
# Python
ruff check --fix .

# JavaScript
eslint --fix src/
```

---

### 4. Type Checking ✅

**Run type checker**:
```bash
# Python
mypy src/

# TypeScript
tsc --noEmit

# Go (built-in)
go build
```

**Expected**:
- ✅ **Zero type errors**
- ✅ **All functions typed**
- ✅ **Strict mode enabled**

**Common type issues**:
- Missing type hints
- Incorrect return types
- Type mismatches
- `Any` overuse

---

### 5. Security Scanning ✅

**Run security scanner**:
```bash
# Python
pip-audit

# JavaScript
npm audit

# All languages
snyk test
```

**Expected**:
- ✅ **Zero critical vulnerabilities**
- ✅ **Zero high vulnerabilities**
- ⚠️ **Medium/low documented** (fix when possible)

**If critical/high vulnerabilities found**:
- ❌ **Do NOT commit**
- ✅ **Fix immediately** (update dependencies)
- ✅ **Verify fix with re-scan**

---

### 6. Code Quality ✅

**Manual checks**:
- [ ] **No debug code** (no `print()`, `console.log()`, `debugger`)
- [ ] **No TODOs** (or documented as tech debt)
- [ ] **No commented code** (delete dead code)
- [ ] **No secrets** (no API keys, passwords)
- [ ] **Functions < 50 lines** (refactor if longer)
- [ ] **Clear variable names** (no `x`, `temp`, `data`)

**Automated checks**:
```bash
# Search for debug code
git grep -i "print("
git grep -i "console.log"
git grep "debugger"

# Search for TODOs
git grep -i "TODO"
git grep -i "FIXME"

# Search for secrets
git secrets --scan
truffleHog --regex --entropy=False .
```

---

### 7. Documentation ✅

**Documentation checks**:
- [ ] **Public APIs documented** (docstrings/JSDoc)
- [ ] **Complex logic explained** (comments where needed)
- [ ] **README updated** (if new features)
- [ ] **Changelog updated** (if project uses one)
- [ ] **Examples provided** (for new features)

**Verify docstrings**:
```bash
# Python (check for missing docstrings)
pydocstyle src/

# Generate docs to verify
sphinx-build -b html docs/ docs/_build/
```

---

### 8. Git Status Clean ✅

**Check git status**:
```bash
git status
```

**Expected**:
- ✅ **Only intended files staged**
- ✅ **No untracked files** (or add to `.gitignore`)
- ✅ **No large files** (< 1 MB ideally)

**Common issues**:
- Accidentally staged test data
- Accidentally staged environment files (`.env`)
- Accidentally staged build artifacts (`dist/`, `*.pyc`)

**Clean up**:
```bash
# Unstage unintended files
git reset HEAD file.txt

# Remove from staging
git rm --cached file.txt
```

---

## Automated Pre-Commit Hooks

### Install Pre-Commit Framework

**Install** (one-time setup):
```bash
# Python
pip install pre-commit

# Or use uv
uv pip install pre-commit

# Install hooks
pre-commit install
```

### Configure Hooks

**.pre-commit-config.yaml** (repository root):
```yaml
repos:
  # Python formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff-format
        name: Format Python code
      - id: ruff
        name: Lint Python code
        args: [--fix, --exit-non-zero-on-fix]
  
  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        name: Type check Python code
        additional_dependencies: [types-requests]
  
  # JavaScript/TypeScript
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        name: Format JS/TS/JSON/YAML
  
  # General checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
        name: Trim trailing whitespace
      - id: end-of-file-fixer
        name: Fix end of files
      - id: check-yaml
        name: Check YAML syntax
      - id: check-added-large-files
        name: Prevent large files
        args: [--maxkb=1000]
      - id: check-toml
        name: Check TOML syntax
      - id: debug-statements
        name: Check for debug statements
  
  # Security
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        name: Detect secrets
        args: [--baseline, .secrets.baseline]
```

### Run Pre-Commit Manually

**Run all hooks**:
```bash
pre-commit run --all-files
```

**Run specific hook**:
```bash
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

**Expected output** (all passing):
```
Trim trailing whitespace...................Passed
Fix end of files...........................Passed
Check yaml.................................Passed
Check for added large files................Passed
Check toml.................................Passed
Debug statements (python)..................Passed
Format Python code.........................Passed
Lint Python code...........................Passed
Type check Python code.....................Passed
Format JS/TS/JSON/YAML.....................Passed
Detect secrets.............................Passed
```

---

## Bypass Pre-Commit (Rare Cases)

### When to Bypass

**NEVER bypass for**:
- ❌ Failing tests
- ❌ Security vulnerabilities
- ❌ Type errors
- ❌ Linting errors

**Rarely acceptable** (with justification):
- ⚠️ Work-in-progress commit (feature not done)
- ⚠️ Emergency hotfix (document why)
- ⚠️ External file import (not your code)

### How to Bypass

**Bypass all hooks** (not recommended):
```bash
git commit --no-verify -m "WIP: Feature in progress"
```

**Bypass specific hook** (configure in YAML):
```yaml
# Skip specific files
- id: mypy
  exclude: ^legacy/  # Skip legacy code
```

**Document bypass**:
```bash
git commit --no-verify -m "hotfix: Fix critical production bug

Bypassing pre-commit due to urgent production issue.
Will address linting issues in follow-up PR.

Emergency-Hotfix: PROD-2024-001
"
```

---

## Commit Message Standards

### Conventional Commits Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, whitespace)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding/updating tests
- `chore`: Maintenance (dependencies, config)
- `security`: Security fix/improvement

**Examples**:
```bash
# Feature
git commit -m "feat(confluence): Add attachment upload operation"

# Bug fix
git commit -m "fix: Handle timeout for large file uploads

Increased timeout from 30s to 120s for files >100MB.
Found during UAT testing.

Fixes: #42
"

# Documentation
git commit -m "docs: Update API reference with examples"

# Security
git commit -m "security: Update requests to 2.31.0 (CVE-2023-32681)

Addresses medium severity session fixation vulnerability.

CVE: CVE-2023-32681
CVSS: 6.1 (MEDIUM)
Package: requests 2.27.0 → 2.31.0

Security-Issue: CVE-2023-32681
"
```

---

## Pre-Commit Workflow

### Standard Workflow

```
1. Make code changes
   ├─ Implement feature
   ├─ Write tests
   └─ Add documentation

2. Run tests locally
   └─ pytest -v  # All pass ✅

3. Run pre-commit
   └─ pre-commit run --all-files  # All pass ✅

4. Stage changes
   └─ git add src/ tests/ docs/

5. Commit
   └─ git commit -m "feat: Add new feature"
   └─ Pre-commit hooks run automatically ✅

6. Push
   └─ git push origin feature/branch
```

### If Pre-Commit Fails

```
1. Pre-commit runs (automatic on commit)
   └─ Hook fails ❌

2. Review failure output
   └─ Read error messages

3. Fix issues
   └─ Format code, fix linting, etc.

4. Re-run pre-commit
   └─ pre-commit run --all-files

5. Re-stage fixed files
   └─ git add src/

6. Re-commit
   └─ git commit -m "feat: Add new feature"
   └─ Hooks pass ✅
```

---

## CI/CD Integration

### Verify in Pipeline

**Even with pre-commit hooks, run in CI/CD** (catches bypassed commits):

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
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pre-commit
      
      - name: Run tests
        run: pytest --cov=src --cov-fail-under=80
      
      - name: Run pre-commit
        run: pre-commit run --all-files
      
      - name: Security scan
        run: pip-audit
```

---

## Quick Reference

### One-Command Verification

**Create verification script** (`scripts/verify.sh`):
```bash
#!/bin/bash
set -e  # Exit on error

echo "🧪 Running tests..."
pytest -v

echo "🎨 Checking code formatting..."
ruff format --check .

echo "🔍 Running linter..."
ruff check .

echo "🔒 Type checking..."
mypy src/

echo "🔐 Security scan..."
pip-audit

echo "✨ Running pre-commit hooks..."
pre-commit run --all-files

echo "✅ All checks passed! Ready to commit."
```

**Run before commit**:
```bash
./scripts/verify.sh
```

---

## Key Takeaways

**Remember**:
- 🚦 **Pre-commit is final gate** (don't bypass)
- 🚦 **Automate with hooks** (consistent enforcement)
- 🚦 **Fix issues immediately** (don't defer)
- 🚦 **All checks must pass** (tests, lint, type, security)
- 🚦 **Document bypasses** (rare, with justification)

**Philosophy**:
> "Pre-commit verification is not a suggestion—it's a requirement. If code doesn't pass pre-commit, it doesn't belong in version control."

**Culture**:
> "Quality is enforced automatically. Pre-commit hooks ensure no broken code enters the codebase, saving time and preventing bugs."

---

**Related**:
- [Code Quality Standards](code-quality-standards.md) - Standards enforced by pre-commit
- [Testing Requirements](testing-requirements.md) - Test standards
- [Security Vulnerability Management](../philosophy/security-vulnerability-management.md) - Security scanning
- [Development Workflow](../processes/development-workflow.md) - Phase 7: Pre-commit verification
