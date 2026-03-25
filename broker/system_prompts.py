"""Helpers for loading broker system prompts from markdown files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_SYSTEM_PROMPTS_DIR = Path("broker") / "system_prompts"
DEFAULT_SYSTEM_PROMPT_FILENAME = "default.system.prompt.md"


def default_system_prompts_dir(workspace_root: Path) -> Path:
    """Return the default system prompt directory for the workspace."""
    return (workspace_root / DEFAULT_SYSTEM_PROMPTS_DIR).resolve()


def _ensure_within_workspace(path: Path, workspace_root: Path) -> Path:
    resolved = path.resolve()
    workspace = workspace_root.resolve()
    if not resolved.is_relative_to(workspace):
        raise ValueError(
            "system prompt path must stay inside the workspace root: %s" % resolved
        )
    return resolved


def resolve_system_prompt_path(
    candidate: str | Path,
    *,
    workspace_root: Path,
    prompts_dir: Path,
) -> Path:
    """Resolve a system prompt candidate into one workspace-local markdown path."""
    value = str(candidate).strip()
    if not value:
        value = DEFAULT_SYSTEM_PROMPT_FILENAME

    raw_path = Path(value)
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    elif raw_path.parent == Path("."):
        resolved = (prompts_dir / raw_path.name).resolve()
    else:
        resolved = (workspace_root / raw_path).resolve()

    resolved = _ensure_within_workspace(resolved, workspace_root)
    if not resolved.is_file():
        raise ValueError("system prompt file was not found: %s" % resolved)
    return resolved


def load_system_prompt_text(path: Path) -> str:
    """Read one markdown-backed system prompt and validate it is not empty."""
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError("system prompt file is empty: %s" % path)
    return content


@dataclass(frozen=True)
class ResolvedSystemPrompt:
    """Loaded system prompt content and the file source, when applicable."""

    content: str
    source_path: Optional[Path] = None


class SystemPromptLoader:
    """Resolve inline or file-backed system prompts for broker sessions."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        prompts_dir: Path,
        default_prompt_path: Path,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.prompts_dir = _ensure_within_workspace(prompts_dir, self.workspace_root)
        self.default_prompt_path = _ensure_within_workspace(
            default_prompt_path,
            self.workspace_root,
        )

    def resolve(
        self,
        *,
        inline_prompt: Optional[str] = None,
        prompt_path: Optional[str] = None,
    ) -> ResolvedSystemPrompt:
        """Return the effective system prompt for one request or session."""
        if isinstance(inline_prompt, str) and inline_prompt.strip():
            return ResolvedSystemPrompt(content=inline_prompt.strip(), source_path=None)

        if isinstance(prompt_path, str) and prompt_path.strip():
            resolved_path = resolve_system_prompt_path(
                prompt_path,
                workspace_root=self.workspace_root,
                prompts_dir=self.prompts_dir,
            )
        else:
            resolved_path = self.default_prompt_path

        return ResolvedSystemPrompt(
            content=load_system_prompt_text(resolved_path),
            source_path=resolved_path,
        )
