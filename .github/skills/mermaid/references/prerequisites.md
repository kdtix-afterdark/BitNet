# Mermaid Skill Prerequisites

Use these checks before Mermaid work.

## Modes

- `syntax`:
  - requires `python3`
- `render`:
  - requires `python3`
  - requires `node`
  - requires `npm`
  - requires `npx`
- `closed-loop`:
  - requires all render prerequisites
  - requires Playwright Chromium

## Base checks

```bash
command -v python3 >/dev/null 2>&1
command -v node >/dev/null 2>&1
command -v npm >/dev/null 2>&1
command -v npx >/dev/null 2>&1
```

## Renderer check

Prefer the exact-match local Mermaid toolchain when the workspace has a syntax manifest:

```bash
python3 ~/.codex/skills/mermaid/scripts/check_env.py --workspace-root "$PWD"
```

In `nlplogix` workspaces, the preferred remediation is:

```bash
cd ./nlplogix/tools/mermaid-cli && npm install
```

If that is unavailable, rendering requires either:

- a workspace-pinned Mermaid CLI toolchain, or
- a renderer that exactly matches the local syntax manifest

## Playwright check

Preferred closed-loop dependency model:

- Node Playwright runtime
- Chromium installed for Playwright

Checks:

```bash
npx playwright --version
npx playwright install chromium
```

If the workspace still uses Python Playwright, use:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

## Missing-prerequisite responses

If `python3` is missing, stop.

If `npx` is missing, do not attempt render or closed-loop work.

If Chromium is missing, do not run browser-based visual QA. Downgrade to `render` mode unless the user explicitly requested closed-loop inspection.

## Optional LLM repair

Model-driven Mermaid repair is optional. It is not a prerequisite for `syntax`, `render`, or baseline `closed-loop` mode.

Use it only when all of these are true:

- `OPENAI_API_KEY` is set, or `AZURE_OPENAI_ENDPOINT` plus `AZURE_OPENAI_API_KEY` are set
- the deterministic loop has stalled or still failed
- the user wants automatic Mermaid source repair beyond theme and CSS heuristics

Example:

```bash
python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --enable-llm-repair --write-patches
AZURE_OPENAI_ENDPOINT=... AZURE_OPENAI_API_KEY=... AZURE_OPENAI_DEPLOYMENT=... python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --enable-llm-repair --llm-provider azure-openai --write-patches
python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --env-file "$PWD/.env.mermaid.local" --enable-llm-repair --llm-provider azure-openai --write-patches
python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --project-json "$PWD/project.json" --enable-llm-repair --llm-provider azure-openai --write-patches
```

Wizard setup:

```bash
python3 ~/.codex/skills/mermaid/scripts/setup_azure_openai_env.py
python3 ~/.codex/skills/mermaid/scripts/setup_azure_openai_env.py --format shell --write-file ~/.config/codex/mermaid-azure.sh
source ~/.config/codex/mermaid-azure.sh
python3 ~/.codex/skills/mermaid/scripts/setup_azure_openai_env.py --format dotenv --write-file ./.env.mermaid.local
python3 ~/.codex/skills/mermaid/scripts/run_llm_repair_fixtures.py --workspace-root "$PWD" --env-file "$PWD/.env.mermaid.local" --llm-provider azure-openai
```

## User-facing summary

Report capability like this:

```text
Mermaid Environment
  Syntax mode   : available
  Render mode   : available
  Closed-loop   : unavailable
  Blocker       : Chromium not installed for Playwright
  Next step     : npx playwright install chromium
```
