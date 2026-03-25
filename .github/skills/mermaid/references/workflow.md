# Mermaid Closed-Loop Workflow

Use this loop when the user wants the diagram improved, not just validated.

## Objective

For each Mermaid diagram:

1. validate syntax against the active Mermaid version
2. render light and dark variants
3. inspect visually
4. apply the smallest safe fix
5. repeat until both variants pass or stop improving

## Inputs

- `.mmd` files or Markdown Mermaid blocks
- Mermaid version manifest
- diagram-type syntax reference
- light and dark theme profiles
- optional LLM config from env vars, `.env.mermaid.local`, or `project.json`

## Acceptance bar

A diagram passes only if:

- syntax validates
- it renders without parser or runtime errors
- labels are not clipped
- overlap is not material
- text is readable on the target background
- theme colors are consistent with the requested palette

## Loop

1. Discover diagrams.
2. Detect diagram type.
3. Read the Mermaid version manifest.
4. Load only the syntax reference for that type.
5. Validate syntax and fix syntax-only failures first.
6. Render a baseline matrix:
   - light
   - dark
7. Inspect the render:
   - screenshot review
   - SVG or DOM bounding-box review when available
8. Score failures:
   - clipping
   - overlap
   - contrast
   - density
   - palette consistency
9. Apply the smallest safe fix in this order:
   - `themeVariables`
   - `classDef` or `style`
   - directional or spacing changes
   - label wrapping or shortening
   - structural rewrite only as a last resort
10. If deterministic fixes stall and model repair is enabled, send the Mermaid body, pinned version, render failures, and the relevant syntax cache excerpt to the model.
11. Re-render and compare.
12. Keep the model-authored Mermaid only if it improves the score in the same light/dark loop.
13. Stop when both variants pass or the score stops improving.

## Change order

Keep this order:

1. syntax correctness
2. render stability
3. theme variables
4. local styling
5. diagram structure

## Workspace-first tooling

If the repo already has Mermaid tooling, prefer that first:

- `nlplogix/scripts/syntax_reference_loader.py`
- `nlplogix/scripts/update-syntax-cache.py`
- `nlplogix/scripts/convert_mermaid_to_svg.py`
- `nlplogix/scripts/apply_mermaid_theme.py`
- `nlplogix/scripts/inspect_mermaid_colors.py`

If not, recreate only the minimum needed for the current task.
