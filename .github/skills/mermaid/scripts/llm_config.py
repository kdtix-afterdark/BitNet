#!/usr/bin/env python3
"""
Shared LLM configuration discovery for the Mermaid skill.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from typing import Mapping


DEFAULT_AZURE_API_VERSION = "2024-05-01-preview"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def find_default_env_file(workspace_root: Path) -> Path | None:
    candidate = workspace_root / ".env.mermaid.local"
    return candidate if candidate.exists() else None


def find_default_project_json(workspace_root: Path) -> tuple[Path | None, str | None]:
    root_candidate = workspace_root / "project.json"
    if root_candidate.exists():
        return root_candidate, None

    nlplogix_root = workspace_root / "nlplogix"
    if not nlplogix_root.exists():
        return None, None

    nested = sorted(nlplogix_root.glob("*/*/project.json"))
    if len(nested) == 1:
        return nested[0], None
    if len(nested) > 1:
        return None, "multiple project.json files found under nlplogix; pass --project-json to disambiguate"
    return None, None


def load_workspace_llm_config(
    workspace_root: Path,
    *,
    env: Mapping[str, str] | None = None,
    env_file: str | Path | None = None,
    project_json: str | Path | None = None,
) -> dict[str, Any]:
    env_map = dict(env or os.environ)

    env_file_path = Path(env_file).expanduser() if env_file else find_default_env_file(workspace_root)
    env_file_values = _parse_dotenv(env_file_path) if env_file_path and env_file_path.exists() else {}

    project_json_path: Path | None
    project_json_notice: str | None = None
    if project_json:
        project_json_path = Path(project_json).expanduser()
    else:
        project_json_path, project_json_notice = find_default_project_json(workspace_root)

    project_data = _read_json(project_json_path) if project_json_path and project_json_path.exists() else {}
    llm_section = project_data.get("llm", {}) if isinstance(project_data, dict) else {}
    if not isinstance(llm_section, dict):
        llm_section = {}
    azure_section = llm_section.get("azureOpenai", {})
    if not isinstance(azure_section, dict):
        azure_section = {}
    openai_section = llm_section.get("openai", {})
    if not isinstance(openai_section, dict):
        openai_section = {}

    provider = (
        env_map.get("MERMAID_LLM_PROVIDER")
        or env_file_values.get("MERMAID_LLM_PROVIDER")
        or llm_section.get("provider")
    )
    openai_api_key = (
        env_map.get("OPENAI_API_KEY")
        or env_file_values.get("OPENAI_API_KEY")
        or openai_section.get("apiKey")
    )
    openai_model = (
        env_map.get("OPENAI_MODEL")
        or env_file_values.get("OPENAI_MODEL")
        or openai_section.get("model")
    )
    azure_endpoint = (
        env_map.get("AZURE_OPENAI_ENDPOINT")
        or env_file_values.get("AZURE_OPENAI_ENDPOINT")
        or azure_section.get("endpoint")
    )
    azure_api_key = (
        env_map.get("AZURE_OPENAI_API_KEY")
        or env_file_values.get("AZURE_OPENAI_API_KEY")
        or azure_section.get("apiKey")
    )
    azure_deployment = (
        env_map.get("AZURE_OPENAI_DEPLOYMENT")
        or env_file_values.get("AZURE_OPENAI_DEPLOYMENT")
        or azure_section.get("deployment")
    )
    azure_api_version = (
        env_map.get("AZURE_OPENAI_API_VERSION")
        or env_file_values.get("AZURE_OPENAI_API_VERSION")
        or azure_section.get("apiVersion")
        or DEFAULT_AZURE_API_VERSION
    )

    if not provider:
        if openai_api_key:
            provider = "openai"
        elif azure_endpoint and azure_api_key:
            provider = "azure-openai"

    return {
        "provider": provider,
        "openai_api_key": openai_api_key,
        "openai_model": openai_model,
        "azure_endpoint": azure_endpoint,
        "azure_api_key": azure_api_key,
        "azure_deployment": azure_deployment,
        "azure_api_version": azure_api_version,
        "env_file_path": str(env_file_path) if env_file_path and env_file_path.exists() else None,
        "project_json_path": str(project_json_path) if project_json_path and project_json_path.exists() else None,
        "project_json_notice": project_json_notice,
    }
