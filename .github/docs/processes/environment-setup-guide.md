# Environment Setup Guide

> **Consistent environments = fewer surprises**: Use devcontainers for reproducible development.

---

## Overview

A consistent development environment prevents "works on my machine" problems and ensures all team members (and AI agents) work with the same tools, dependencies, and configurations.

**Primary recommendation**: **Devcontainers** (Docker-based development environments)

**Why devcontainers**:
- ✅ Identical environment for all developers
- ✅ No "works on my machine" issues
- ✅ Cross-platform compatibility (Windows, macOS, Linux)
- ✅ Version-controlled environment configuration
- ✅ AI agent compatibility (GitHub Copilot, Cursor, etc.)
- ✅ Zero-config onboarding for new team members
- ✅ Isolated dependencies (no global conflicts)

---

## What is a Devcontainer?

A **devcontainer** is a Docker container configured specifically for development. It includes:
- Language runtime (Python, Node.js, Go, etc.)
- Development tools (debugger, linter, formatter)
- IDE extensions and settings
- Project dependencies
- Environment variables and configurations

**Configuration file**: `.devcontainer/devcontainer.json`

**How it works**:
1. IDE (VS Code, Cursor, etc.) reads `.devcontainer/devcontainer.json`
2. Builds or pulls Docker image with specified tools
3. Mounts your code into the container
4. Connects IDE to containerized environment
5. You develop inside the container (transparent to you)

**Result**: Every developer gets the same environment, regardless of host OS.

---

## Quick Start: Devcontainer Setup

### Prerequisites

**Install Docker**:
- **Windows**: Docker Desktop (WSL 2 backend recommended)
- **macOS**: Docker Desktop
- **Linux**: Docker Engine

**Install IDE with devcontainer support**:
- VS Code + [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Cursor (built-in support)
- GitHub Codespaces (cloud-based, built-in)

---

### Step 1: Create Devcontainer Configuration

Create `.devcontainer/devcontainer.json` in repository root:

**Python project example**:
```json
{
  "name": "Python 3.12 Dev Environment",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "ms-python.debugpy"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "python.formatting.provider": "none",
        "[python]": {
          "editor.defaultFormatter": "charliermarsh.ruff",
          "editor.formatOnSave": true,
          "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
          }
        }
      }
    }
  },
  
  "postCreateCommand": "pip install --upgrade pip && pip install -e '.[dev]'",
  
  "forwardPorts": [8000],
  
  "remoteUser": "vscode"
}
```

**Node.js project example**:
```json
{
  "name": "Node.js 20 Dev Environment",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ms-vscode.vscode-typescript-next"
      ],
      "settings": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
          "source.fixAll.eslint": "explicit"
        }
      }
    }
  },
  
  "postCreateCommand": "npm install",
  
  "forwardPorts": [3000],
  
  "remoteUser": "node"
}
```

---

### Step 2: Open Project in Devcontainer

**VS Code / Cursor**:
1. Open project folder
2. Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
3. Select: "Dev Containers: Reopen in Container"
4. Wait for container build (first time only, ~2-5 minutes)
5. IDE reconnects inside container
6. Start coding!

**Indicator**: Look for "Dev Container: [name]" in bottom-left corner of IDE.

**GitHub Codespaces** (cloud-based):
1. Navigate to repository on GitHub
2. Click "Code" → "Codespaces" → "Create codespace on main"
3. Browser opens with VS Code interface
4. Devcontainer auto-loads
5. Start coding in the cloud!

---

## Devcontainer Configuration Deep Dive

### Basic Structure

```json
{
  "name": "Project Name",              // Display name in IDE
  "image": "image:tag",                 // Pre-built Docker image
  // OR
  "dockerFile": "Dockerfile",           // Custom Dockerfile
  
  "customizations": { /* IDE settings */ },
  "postCreateCommand": "setup script",  // Run after container created
  "forwardPorts": [8000],               // Expose ports to host
  "remoteUser": "vscode"                // User inside container
}
```

---

### Using Pre-Built Images

**Microsoft devcontainer images** (recommended):
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.12"
}
```

**Available images**:
- `python:3.10`, `python:3.11`, `python:3.12`
- `javascript-node:18`, `javascript-node:20`
- `typescript-node:20`
- `go:1.21`
- `rust:1.75`
- `java:17`, `java:21`
- `dotnet:8.0`
- `universal:2` (multi-language)

**Browse all images**: https://github.com/devcontainers/images

---

### Using Custom Dockerfile

For complex setups, use a custom Dockerfile:

**.devcontainer/Dockerfile**:
```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python tools
RUN pip install --upgrade pip uv

# Set working directory
WORKDIR /workspace
```

**.devcontainer/devcontainer.json**:
```json
{
  "name": "Custom Python Environment",
  "dockerFile": "Dockerfile",
  "context": "..",
  "workspaceFolder": "/workspace"
}
```

---

### IDE Customizations

**VS Code / Cursor extensions** (auto-install):
```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",              // Python support
        "ms-python.debugpy",             // Python debugger
        "charliermarsh.ruff",            // Ruff linter/formatter
        "GitHub.copilot",                // GitHub Copilot
        "eamodio.gitlens",               // Git history
        "mhutchie.git-graph"             // Git graph visualization
      ]
    }
  }
}
```

**IDE settings** (auto-configure):
```json
{
  "customizations": {
    "vscode": {
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.testing.pytestEnabled": true,
        "python.testing.unittestEnabled": false,
        "editor.formatOnSave": true,
        "editor.rulers": [88],
        "files.trimTrailingWhitespace": true,
        "terminal.integrated.defaultProfile.linux": "bash"
      }
    }
  }
}
```

---

### Lifecycle Scripts

**postCreateCommand** (runs once after container created):
```json
{
  "postCreateCommand": "pip install -e '.[dev]' && pre-commit install"
}
```

**postStartCommand** (runs every time container starts):
```json
{
  "postStartCommand": "echo 'Container started!'"
}
```

**postAttachCommand** (runs when IDE attaches):
```json
{
  "postAttachCommand": "git status"
}
```

**Use cases**:
- `postCreateCommand`: Install dependencies, run migrations
- `postStartCommand`: Start background services
- `postAttachCommand`: Display status info

---

### Port Forwarding

**Forward ports to host**:
```json
{
  "forwardPorts": [8000, 5432, 6379],
  "portsAttributes": {
    "8000": {
      "label": "Web Server",
      "onAutoForward": "notify"
    },
    "5432": {
      "label": "PostgreSQL"
    },
    "6379": {
      "label": "Redis"
    }
  }
}
```

**Access from host**:
- Container port `8000` → `http://localhost:8000`
- Automatic port forwarding (transparent)

---

### Features (Add Tools On-Demand)

**Dev Container Features** (composable tooling):
```json
{
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    }
  }
}
```

**Available features**: https://containers.dev/features

---

## Multi-Service Development (Docker Compose)

For projects with multiple services (database, cache, API, etc.), use Docker Compose:

**.devcontainer/docker-compose.yml**:
```yaml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
    command: sleep infinity
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/myapp
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: myapp
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7
    restart: unless-stopped

volumes:
  postgres-data:
```

**.devcontainer/devcontainer.json**:
```json
{
  "name": "Multi-Service App",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"]
    }
  },
  
  "forwardPorts": [8000, 5432, 6379],
  
  "postCreateCommand": "pip install -e '.[dev]'"
}
```

**Benefits**:
- All services start automatically
- Network connectivity between services
- Realistic production-like environment
- Isolated from host system

---

## Devcontainer Templates

### Python (FastAPI/Django)

```json
{
  "name": "Python Web App",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.debugpy",
        "charliermarsh.ruff",
        "GitHub.copilot"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.testing.pytestEnabled": true,
        "[python]": {
          "editor.defaultFormatter": "charliermarsh.ruff",
          "editor.formatOnSave": true
        }
      }
    }
  },
  
  "postCreateCommand": "pip install --upgrade pip uv && uv sync --frozen --all-extras --dev",
  
  "forwardPorts": [8000],
  
  "remoteUser": "vscode"
}
```

---

### Node.js (React/Next.js)

```json
{
  "name": "Node.js Web App",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
  
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "GitHub.copilot",
        "bradlc.vscode-tailwindcss"
      ],
      "settings": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
          "source.fixAll.eslint": "explicit"
        }
      }
    }
  },
  
  "postCreateCommand": "npm install",
  
  "forwardPorts": [3000],
  
  "remoteUser": "node"
}
```

---

### Go

```json
{
  "name": "Go App",
  "image": "mcr.microsoft.com/devcontainers/go:1.22",
  
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  
  "customizations": {
    "vscode": {
      "extensions": [
        "golang.go",
        "GitHub.copilot"
      ],
      "settings": {
        "go.toolsManagement.autoUpdate": true,
        "go.useLanguageServer": true,
        "[go]": {
          "editor.formatOnSave": true,
          "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
          }
        }
      }
    }
  },
  
  "postCreateCommand": "go mod download",
  
  "forwardPorts": [8080],
  
  "remoteUser": "vscode"
}
```

---

## IDE-Specific Setup

### VS Code

**Install extension**:
1. Open VS Code
2. Extensions panel (`Ctrl+Shift+X`)
3. Search "Dev Containers"
4. Install "Dev Containers" by Microsoft

**Open in devcontainer**:
- Command Palette → "Dev Containers: Reopen in Container"
- Or click notification: "Reopen in Container"

**Rebuild container** (after config changes):
- Command Palette → "Dev Containers: Rebuild Container"

---

### Cursor

**Built-in support** (no extension needed):
1. Open project with `.devcontainer/devcontainer.json`
2. Cursor detects configuration automatically
3. Notification: "Open in Dev Container?"
4. Click "Reopen in Container"

**AI features work inside container** (GitHub Copilot, Cursor AI).

---

### GitHub Codespaces

**Cloud-based devcontainers** (no Docker install needed):

**From GitHub.com**:
1. Navigate to repository
2. Click "Code" button
3. Click "Codespaces" tab
4. Click "Create codespace on main"
5. VS Code opens in browser

**From VS Code**:
1. Install "GitHub Codespaces" extension
2. Command Palette → "Codespaces: Create New Codespace"
3. Select repository and branch

**Pricing**: Free tier includes 60 hours/month (2-core).

---

### JetBrains IDEs (IntelliJ, PyCharm, etc.)

**Dev Containers support** (since 2023.3):
1. Install Docker plugin
2. Open project
3. Settings → Build, Execution, Deployment → Docker
4. Add Docker configuration
5. Run → Run in Dev Container

**Alternative**: Use Gateway + Codespaces for cloud development.

---

## Alternative Approaches

### When NOT to Use Devcontainers

**Skip devcontainers if**:
- ❌ Single-person hobby project (overhead not justified)
- ❌ Lightweight scripting (Python/Node installed globally is fine)
- ❌ Docker not available (corporate restrictions, old hardware)
- ❌ IDE doesn't support devcontainers (rare)

**Use alternatives below instead**.

---

### Alternative 1: Virtual Environments (Python)

**For Python projects without Docker**:

**venv** (built-in):
```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -e '.[dev]'

# Deactivate
deactivate
```

**uv** (modern, fast):
```bash
# Install uv
pip install uv

# Create venv and install deps
uv sync --frozen --all-extras --dev

# Activate
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

**Pros**: Simple, no Docker needed  
**Cons**: Platform-specific (Python version, system deps differ)

---

### Alternative 2: Docker Standalone

**Run commands in Docker without devcontainer**:

```bash
# Run tests in Docker
docker run -v $(pwd):/app -w /app python:3.12 pytest

# Run linter
docker run -v $(pwd):/app -w /app python:3.12 ruff check .

# Interactive shell
docker run -it -v $(pwd):/app -w /app python:3.12 bash
```

**Pros**: Consistent environment, no IDE integration needed  
**Cons**: Manual, not integrated with IDE (no debugging, autocomplete)

---

### Alternative 3: Native Installation

**Install tools directly on host OS**:

**Python**:
```bash
# macOS (Homebrew)
brew install python@3.12

# Ubuntu
sudo apt install python3.12

# Windows
# Download from python.org
```

**Node.js**:
```bash
# macOS
brew install node@20

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from nodejs.org or use nvm-windows
```

**Pros**: Fastest (no container overhead), direct access  
**Cons**: Platform-specific issues, version conflicts, "works on my machine"

---

## Troubleshooting

### Container Won't Build

**Error**: `failed to solve with frontend dockerfile.v0`

**Solution**: Update Docker Desktop to latest version.

---

**Error**: `cannot connect to Docker daemon`

**Solution**:
- Ensure Docker Desktop is running
- Linux: Add user to `docker` group: `sudo usermod -aG docker $USER`

---

### Slow Performance (Windows)

**Problem**: File I/O slow on Windows with WSL 2 backend.

**Solution**: Store project files inside WSL 2 filesystem, not Windows (`/mnt/c/`):

```bash
# ❌ Slow (Windows filesystem)
cd /mnt/c/Users/username/project

# ✅ Fast (WSL 2 filesystem)
cd ~/project
```

Clone repositories directly in WSL:
```bash
# From WSL terminal
cd ~
git clone https://github.com/org/repo.git
code repo  # Opens in VS Code with devcontainer
```

---

### Extensions Not Installing

**Problem**: VS Code extensions fail to install in container.

**Solution**: Check `customizations.vscode.extensions` array syntax:
```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",    // ✅ Correct
        "python"               // ❌ Wrong (missing publisher)
      ]
    }
  }
}
```

Find correct extension ID:
1. Extensions panel in VS Code
2. Click extension
3. Copy "Identifier" (e.g., `ms-python.python`)

---

### Port Already in Use

**Error**: `port 8000 is already allocated`

**Solution**:
```bash
# Find process using port
lsof -i :8000      # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or use different port in devcontainer.json
{
  "forwardPorts": [8001]  // Changed from 8000
}
```

---

### Container Keeps Restarting

**Problem**: Container exits immediately after starting.

**Solution**: Check `postCreateCommand` for errors:
```bash
# View container logs
docker logs <container-id>

# Test command manually
docker run -it <image> bash
# Run command that's failing
```

Fix command in `devcontainer.json`, then rebuild.

---

## Best Practices

### Version Control

**Commit devcontainer config**:
```bash
git add .devcontainer/
git commit -m "Add devcontainer configuration"
```

**Do NOT commit**:
- `.vscode/settings.json` (personal IDE settings)
- IDE-specific files outside `.devcontainer/`

---

### Keep Images Updated

**Rebuild periodically** to get security updates:
```bash
# VS Code: Command Palette
Dev Containers: Rebuild Container

# Or pull latest image
docker pull mcr.microsoft.com/devcontainers/python:3.12
```

**Pin versions for stability** (production):
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.12.1"
}
```

---

### Minimize Image Size

**Use specific images** (not `universal`):
```json
// ❌ Large (includes everything)
{
  "image": "mcr.microsoft.com/devcontainers/universal:2"
}

// ✅ Smaller (only what you need)
{
  "image": "mcr.microsoft.com/devcontainers/python:3.12"
}
```

**Use `.dockerignore`**:
```
.git
.venv
__pycache__
*.pyc
node_modules
.pytest_cache
```

---

### Document Environment Setup

**README.md** (for new team members):
```markdown
## Development Setup

This project uses devcontainers for consistent environments.

**Prerequisites**:
- Docker Desktop
- VS Code + Dev Containers extension (or Cursor)

**Getting started**:
1. Clone repository: `git clone <url>`
2. Open in VS Code: `code project-name`
3. When prompted, click "Reopen in Container"
4. Wait for container build (~3 minutes first time)
5. Start coding!

**Without devcontainers**:
See [Alternative Setup](#alternative-setup) below.
```

---

### Security

**Don't commit secrets** in devcontainer config:
```json
// ❌ Wrong (secret in version control)
{
  "containerEnv": {
    "API_KEY": "sk-1234567890"
  }
}

// ✅ Right (use .env file, not committed)
{
  "runArgs": ["--env-file", ".env"]
}
```

**.gitignore**:
```
.env
.env.local
```

---

## Checklist

**Setting up devcontainer**:
- [ ] Docker Desktop installed and running
- [ ] IDE with devcontainer support installed
- [ ] `.devcontainer/devcontainer.json` created
- [ ] Image or Dockerfile specified
- [ ] Required extensions listed
- [ ] Lifecycle commands configured (`postCreateCommand`)
- [ ] Ports forwarded (if needed)
- [ ] Configuration committed to version control
- [ ] README updated with setup instructions
- [ ] Tested: Reopen in container works
- [ ] Tested: Dependencies install successfully
- [ ] Tested: Tests pass inside container
- [ ] Tested: Port forwarding works (if applicable)

---

## Summary

**Primary recommendation**: **Use devcontainers** for all multi-person projects.

**Benefits**:
- ✅ Consistent environments (no "works on my machine")
- ✅ Zero-config onboarding (new team members productive in minutes)
- ✅ Cross-platform compatibility (Windows, macOS, Linux)
- ✅ Version-controlled configuration (environment as code)
- ✅ AI agent compatibility (Copilot, Cursor work seamlessly)

**When to use alternatives**:
- Single-person hobby projects (venv is fine)
- Corporate restrictions (no Docker access)
- Lightweight scripting (global Python/Node is acceptable)

**Start simple**: Use pre-built Microsoft images, add complexity only when needed.

---

## Related Guides

- **[Cross-Platform Considerations](cross-platform-considerations.md)**: Devcontainers solve most cross-platform issues automatically
- **[Development Workflow](development-workflow.md)**: Phase 0 includes environment setup
- **[Pre-Commit Verification](../standards/pre-commit-verification.md)**: Works seamlessly inside devcontainers
- **[Code Quality Standards](../standards/code-quality-standards.md)**: Enforce with devcontainer-installed tools
- **[Azure AI Agent Development](azure-ai-agent-guide.md)**: Devcontainer setup for Azure Functions, APIM, and Next.js projects

---

## References

- [Dev Containers specification](https://containers.dev/)
- [Microsoft devcontainer images](https://github.com/devcontainers/images)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [GitHub Codespaces](https://github.com/features/codespaces)
