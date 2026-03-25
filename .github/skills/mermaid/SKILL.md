---
name: mermaid
description: Version-aware Mermaid diagram validation, repair, rendering, theming, and visual QA. Use when Codex needs to fix Mermaid syntax, apply or iterate light/dark themes, render diagrams, inspect readability, or run a closed-loop Mermaid improvement workflow across `.mmd` files or Markdown Mermaid blocks.
---

# Mermaid

Run Mermaid work in the highest supported mode:

- `syntax`: validate and repair Mermaid syntax
- `render`: render diagrams in one or more themes
- `closed-loop`: validate, render light/dark variants, inspect visually, score, and iterate

## Required Preflight

Before doing Mermaid work, check the environment.

Always check:

```bash
command -v python3 >/dev/null 2>&1
command -v node >/dev/null 2>&1
command -v npm >/dev/null 2>&1
command -v npx >/dev/null 2>&1
```

Capability rules:

- `syntax` mode requires `python3`
- `render` mode requires `python3`, `node`, `npm`, and `npx`
- `closed-loop` mode requires the render prerequisites plus Playwright Chromium

Do not assume global `mmdc` is installed. Prefer the exact-match renderer resolved by `scripts/check_env.py`.

If prerequisites are missing, continue in the highest supported mode unless the user explicitly requested a blocked mode. For exact remediation commands, read `references/prerequisites.md`.

## Skill-Owned Scripts

Prefer the skill-owned scripts first:

- `scripts/check_env.py`
- `scripts/iterate_mermaid.py`
- `scripts/setup_azure_openai_env.py`
- `scripts/run_llm_repair_fixtures.py`

Typical commands:

```bash
python3 ~/.codex/skills/mermaid/scripts/check_env.py --workspace-root "$PWD"
python3 ~/.codex/skills/mermaid/scripts/setup_azure_openai_env.py
python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD"
python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --env-file "$PWD/.env.mermaid.local"
python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --project-json "$PWD/project.json"
python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --enable-llm-repair --write-patches
AZURE_OPENAI_ENDPOINT=... AZURE_OPENAI_API_KEY=... AZURE_OPENAI_DEPLOYMENT=... python3 ~/.codex/skills/mermaid/scripts/iterate_mermaid.py path/to/diagram.mmd --workspace-root "$PWD" --enable-llm-repair --llm-provider azure-openai --write-patches
python3 ~/.codex/skills/mermaid/scripts/run_llm_repair_fixtures.py --workspace-root "$PWD" --env-file "$PWD/.env.mermaid.local" --llm-provider azure-openai
```

Use `iterate_mermaid.py` when the user wants a Mermaid-only closed loop that stays focused on diagram validation, render iteration, and theme/readability improvements without dragging unrelated workspace scripts into scope.
Use `--enable-llm-repair` only when a deterministic pass is insufficient and either `OPENAI_API_KEY` or the Azure OpenAI environment variables are available. The runner will keep the deterministic result unless the model-authored Mermaid body actually scores better in the same light/dark render loop.
Use `setup_azure_openai_env.py` when the user wants a wizard-style setup flow for `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, and `AZURE_OPENAI_API_VERSION`. The script can prompt interactively, validate the config, print exports, or write a sourceable file, but it cannot modify the parent shell directly.
Use `.env.mermaid.local` or `project.json` when the user wants local config discovery instead of manual exports. Resolution order is CLI flag, then real env vars, then `.env.mermaid.local`, then `project.json`.
Use `run_llm_repair_fixtures.py` when the user wants a repeatable regression check for the intentionally broken Mermaid fixtures shipped with the skill.

## Workflow

1. Detect the operating mode.
   If the user asks for syntax fixes only, stay in `syntax`.
   If the user asks to render or theme diagrams, use `render`.
   If the user asks for UX tuning, visual review, screenshot-based inspection, or automatic improvement, use `closed-loop`.

2. Resolve the Mermaid version before making syntax claims.
   Prefer `nlplogix/syntax/SYNTAX_VERSION_MANIFEST.json` when present.
   If the workspace has a Mermaid syntax corpus, use that as the source of truth.

3. Load only the relevant syntax reference.
   Open the syntax file for the detected diagram type instead of loading all Mermaid docs.

4. Fix syntax before touching layout or theme.
   Do not start visual tuning while the diagram is still parser-invalid.

5. Apply theme changes with the smallest safe scope.
   Prefer `theme: 'base'` plus `themeVariables`.
   Use `classDef`, `style`, or diagram-specific overrides only when theme variables are insufficient.

6. In closed-loop mode, render both light and dark variants, inspect them, score them, and iterate until they pass or stop improving.
7. If deterministic Mermaid-only fixes stall, optionally run one model-driven repair pass using the pinned Mermaid version and the diagram-type syntax cache, then accept it only if it improves the render score.

For the detailed loop, read `references/workflow.md`.

## Workspace-Aware Execution

If the workspace already includes Mermaid tooling, reuse it instead of rebuilding it.

The skill-owned scripts may integrate with these repo-local assets when present:

- `nlplogix/scripts/syntax_reference_loader.py`
- `nlplogix/scripts/update-syntax-cache.py`
- `nlplogix/scripts/convert_mermaid_to_svg.py`
- `nlplogix/scripts/apply_mermaid_theme.py`
- `nlplogix/scripts/inspect_mermaid_colors.py`
- `nlplogix/syntax/`
- `nlplogix/themes/`

If those files do not exist, stay within the skill-owned scripts and keep the workflow version-aware.

## Guardrails

- Keep syntax fixes and theme fixes separate whenever possible.
- Prefer the smallest change that improves readability.
- Do not rewrite diagram structure unless styling and spacing changes are insufficient.
- Keep light and dark outputs semantically identical.
- Stop and report version drift if the syntax docs and renderer target different Mermaid versions.
- When visual inspection is unavailable, say so explicitly and call out the remaining UX risk.

## References

Open only what you need:

- `references/prerequisites.md`
- `references/workflow.md`
