# Cross-Platform Considerations

> **Write once, test everywhere**: Practical patterns for cross-platform compatibility.

---

## Overview

When writing code that runs on multiple platforms (Windows, Linux, macOS), certain patterns ensure consistent behavior:

- **File paths**: Use OS-agnostic path separators
- **Line endings**: Handle CRLF (Windows) vs LF (Unix)
- **Signals**: Handle platform-specific signal differences
- **Packages**: Manage platform-specific dependencies
- **Temporary files**: Use platform-agnostic temp directories
- **Environment variables**: Handle case sensitivity

**💡 Best solution**: **[Use devcontainers](environment-setup-guide.md)** to eliminate most cross-platform issues automatically.

---

## Devcontainers: The Cross-Platform Solution

**Problem**: Developers use different operating systems (Windows, macOS, Linux), leading to platform-specific bugs.

**Solution**: **Devcontainers** provide identical Docker-based environments for all developers, regardless of host OS.

**Benefits**:
- ✅ Same environment for everyone (Windows, macOS, Linux)
- ✅ No path separator issues (always Linux inside container)
- ✅ No line ending issues (Git configured in container)
- ✅ No platform-specific dependency issues
- ✅ Consistent Python/Node/Go versions
- ✅ Zero-config onboarding for new team members

**Quick start**:
```json
// .devcontainer/devcontainer.json
{
  "name": "Python 3.12 Dev Environment",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "postCreateCommand": "pip install -e '.[dev]'"
}
```

**Read the full guide**: [Environment Setup Guide](environment-setup-guide.md)

**When to skip devcontainers**:
- Single-person hobby projects (overhead not justified)
- Docker not available (corporate restrictions)
- Lightweight scripting (global Python is fine)

For these cases, follow the patterns below to handle cross-platform differences manually.

---

## File Paths

### Problem

**Windows** uses backslashes: `C:\Users\username\file.txt`  
**Unix/Linux/macOS** use forward slashes: `/home/username/file.txt`

Hardcoded paths break cross-platform compatibility.

### Solution: Use `os.path` or `pathlib`

**❌ Wrong** (platform-specific):
```python
# Breaks on Unix
file_path = "C:\\Users\\username\\file.txt"

# Breaks on Windows
file_path = "/home/username/file.txt"
```

**✅ Right** (cross-platform):
```python
import os

# Option 1: os.path.join()
file_path = os.path.join("path", "to", "file.txt")
# Windows: path\to\file.txt
# Unix: path/to/file.txt

# Option 2: pathlib (modern Python)
from pathlib import Path
file_path = Path("path") / "to" / "file.txt"
```

**Temporary directories**:
```python
import tempfile
import os

# ❌ Wrong (Unix-specific)
temp_dir = "/tmp"

# ✅ Right (cross-platform)
temp_dir = tempfile.gettempdir()
# Windows: C:\Users\...\AppData\Local\Temp
# Unix: /tmp
```

**Absolute paths**:
```python
# ✅ Convert relative to absolute (cross-platform)
abs_path = os.path.abspath("relative/path/file.txt")
```

---

## Line Endings

### Problem

**Windows**: CRLF (`\r\n`)  
**Unix/Linux/macOS**: LF (`\n`)

Git can auto-convert, causing unexpected diff noise or test failures.

### Solution: Configure Git

**.gitattributes** (repository root):
```
# Auto-detect text files
* text=auto

# Force LF for source code
*.py text eol=lf
*.js text eol=lf
*.ts text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.json text eol=lf

# Binary files (no conversion)
*.png binary
*.jpg binary
*.pdf binary
```

**File I/O**:
```python
# ✅ Use universal newlines (handles both)
with open("file.txt", "r", newline="") as f:
    content = f.read()  # Preserves original line endings

# ✅ Or force specific line endings
with open("file.txt", "w", newline="\n") as f:
    f.write("text\n")  # Always LF
```

---

## Signal Handling

### Problem

**Unix/Linux/macOS** have signals like `SIGPIPE`, `SIGHUP`, `SIGTERM`.  
**Windows** doesn't support these signals (raises `AttributeError`).

### Solution: Conditional Signal Handling

**❌ Wrong** (crashes on Windows):
```python
import signal

# Crashes on Windows: module 'signal' has no attribute 'SIGPIPE'
signal.signal(signal.SIGPIPE, handler)
```

**✅ Right** (cross-platform):
```python
import signal

# Option 1: Check if signal exists
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    # Unix: SIGPIPE ignored (prevents broken pipe crashes)
    # Windows: Skipped (signal doesn't exist)
```

**Example from MCP Atlassian**:
```python
def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown.
    
    On Unix/Linux/macOS, ignores SIGPIPE to prevent broken pipe errors
    when client disconnects unexpectedly. On Windows, SIGPIPE doesn't
    exist, so this is safely skipped.
    """
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        logger.debug("SIGPIPE handler configured (Unix/Linux/macOS)")
    else:
        logger.debug("SIGPIPE not available (Windows) - skipped")
```

---

## Platform-Specific Dependencies

### Problem

Some packages are only needed on certain platforms:
- **Windows**: `tzdata` (timezone data not included in Python on Windows)
- **Unix**: Often has system packages that Windows needs separately

### Solution: Conditional Dependencies

**pyproject.toml** (Python):
```toml
[project]
dependencies = [
    "requests>=2.31.0",
    "pydantic>=2.0.0",
]

# Platform-specific dependencies
[project.optional-dependencies]
windows = [
    "tzdata>=2024.1",  # Windows needs timezone data
]

# Install with: pip install -e ".[windows]" (on Windows)
```

**package.json** (JavaScript):
```json
{
  "dependencies": {
    "express": "^4.18.0"
  },
  "optionalDependencies": {
    "fsevents": "^2.3.2"  // macOS-only file watching
  }
}
```

**Check platform in code**:
```python
import sys
import platform

# Check OS
if sys.platform == "win32":
    # Windows-specific code
    pass
elif sys.platform == "darwin":
    # macOS-specific code
    pass
elif sys.platform.startswith("linux"):
    # Linux-specific code
    pass

# Or use platform module
if platform.system() == "Windows":
    # Windows code
    pass
```

---

## Environment Variables

### Problem

**Windows**: Case-insensitive (`PATH` == `Path`)  
**Unix**: Case-sensitive (`PATH` != `Path`)

### Solution: Consistent Naming

```python
import os

# ✅ Use consistent uppercase convention
API_KEY = os.environ.get("JIRA_API_KEY")
BASE_URL = os.environ.get("JIRA_BASE_URL")

# ❌ Avoid mixed case (confusing)
api_key = os.environ.get("jira_api_key")  # Won't work on Unix if set as JIRA_API_KEY
```

---

## File Permissions

### Problem

**Unix/Linux/macOS**: File permissions (read, write, execute) enforced.  
**Windows**: Different permission model (ACLs), less strict for scripts.

### Solution: Assume Stricter Unix Model

```python
import os
import stat

# ✅ Set execute permission (safe on all platforms)
file_path = "script.sh"
os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IXUSR)

# ✅ Check if file is readable
if os.access(file_path, os.R_OK):
    with open(file_path) as f:
        content = f.read()
```

**Docker volumes** (Unix permissions matter):
```yaml
# Ensure files in Docker volumes have correct permissions
volumes:
  - ./data:/data:rw  # Read-write access
```

---

## Testing Cross-Platform

### Test on Each Platform

**CI/CD matrix** (GitHub Actions):
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest
```

### Local Testing

**Docker** (test Linux without dual-boot):
```bash
# Test on Linux container from Windows/macOS
docker run -v $(pwd):/app -w /app python:3.10 pytest
```

**Virtual machines**:
- Test Windows on VM (VirtualBox, VMware, Parallels)
- Test macOS on Mac hardware (Hackintosh unreliable)

---

## Common Pitfalls

### 1. Hardcoded Paths

**❌ Breaks**:
```python
file = "C:\\Users\\user\\file.txt"  # Windows-only
file = "/home/user/file.txt"        # Unix-only
```

**✅ Works**:
```python
file = os.path.join(os.path.expanduser("~"), "file.txt")
# Windows: C:\Users\user\file.txt
# Unix: /home/user/file.txt
```

### 2. Shell Commands

**❌ Breaks**:
```python
import subprocess

# Breaks on Windows (no 'ls' command)
subprocess.run(["ls", "-l"])
```

**✅ Works**:
```python
import os

# Use Python built-ins (cross-platform)
for item in os.listdir("."):
    print(item)

# Or use 'dir' on Windows, 'ls' on Unix
import platform
cmd = "dir" if platform.system() == "Windows" else "ls -l"
subprocess.run(cmd, shell=True)
```

### 3. Assuming Unix Signals

**❌ Breaks**:
```python
signal.signal(signal.SIGPIPE, handler)  # No SIGPIPE on Windows
```

**✅ Works**:
```python
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, handler)
```

### 4. Case-Sensitive Filenames

**❌ Breaks**:
```python
# Unix: file.txt != File.txt
# Windows: file.txt == File.txt (case-insensitive filesystem)
```

**✅ Works**:
```python
# Always use consistent casing
file_path = "file.txt"  # Lowercase convention
```

---

## Quick Reference Checklist

### Before Committing

- [ ] **Paths**: Use `os.path.join()` or `pathlib`, not hardcoded separators
- [ ] **Temp files**: Use `tempfile.gettempdir()`, not `/tmp`
- [ ] **Line endings**: Configured in `.gitattributes`
- [ ] **Signals**: Check `hasattr(signal, "SIGPIPE")` before using
- [ ] **Dependencies**: Platform-specific deps in optional dependencies
- [ ] **Environment vars**: Use uppercase, consistent naming
- [ ] **Shell commands**: Avoid or make platform-specific branches
- [ ] **Tests**: Pass on all target platforms

### During UAT

- [ ] **Test on Windows** (if target platform)
- [ ] **Test on Linux** (if target platform)
- [ ] **Test on macOS** (if target platform)
- [ ] **Document platform differences** (if found)

---

## Real-World Example: MCP Atlassian

### SIGPIPE Fix (Windows Compatibility)

**Before** (crashed on Windows):
```python
signal.signal(signal.SIGPIPE, signal.SIG_IGN)  # AttributeError on Windows
```

**After** (cross-platform):
```python
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
```

### Timezone Data (Windows Requirement)

**Problem**: Windows Python doesn't include timezone data.

**Solution**:
```toml
[project.optional-dependencies]
windows = ["tzdata>=2024.1"]
```

### Path Handling (Cross-Platform Tests)

**Before** (Unix-specific):
```python
temp_dir = "/tmp"
```

**After** (cross-platform):
```python
import tempfile
temp_dir = tempfile.gettempdir()
```

---

## Key Takeaways

**Remember**:
- 🌍 **Use OS-agnostic APIs** (`os.path`, `tempfile`)
- 🌍 **Test on all platforms** (CI/CD matrix)
- 🌍 **Handle platform differences** (signals, dependencies)
- 🌍 **Document quirks** (if found during testing)
- 🌍 **Celebrate cross-platform bugs found** (early discovery!)

**Philosophy**:
> "Write once, test everywhere. Cross-platform compatibility isn't an afterthought—it's a requirement validated from the start."

**Culture**:
> "Finding platform-specific bugs during development is a win. Every bug caught in UAT is a production incident prevented."

---

**Related**:
- [UAT Testing Guide](uat-testing-guide.md) - Cross-platform UAT scenarios
- [Celebrate Early Discovery](../philosophy/celebrate-early-discovery.md) - Celebrate platform bugs found
- [Testing Requirements](../standards/testing-requirements.md) - Platform testing standards
