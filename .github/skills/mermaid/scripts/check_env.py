#!/usr/bin/env python3
"""
Skill-owned Mermaid environment checks.

This script detects the active workspace, resolves the Mermaid renderer that
best matches the local syntax manifest, and reports whether syntax, render,
and closed-loop Mermaid work are currently available.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import llm_config

DEFAULT_MERMAID_VERSION = "11.12.3"
DEFAULT_INSTALL_COMMAND = "cd ./nlplogix/tools/mermaid-cli && npm install"
DEFAULT_LLM_MODEL = "gpt-5.4"
PLAYWRIGHT_CACHE_CANDIDATES = [
    Path.home() / "Library" / "Caches" / "ms-playwright",
    Path.home() / ".cache" / "ms-playwright",
    Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright",
]
CHROMIUM_COMMANDS = [
    "chromium",
    "chromium-browser",
    "google-chrome",
    "chrome",
    "msedge",
]


def _run_command(args: list[str], timeout: int = 10) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 1, "", ""
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _command_path(name: str) -> str | None:
    return shutil.which(name)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_package_version(path: Path) -> str | None:
    data = _read_json(path)
    if not data:
        return None
    version = data.get("version")
    if isinstance(version, str) and version.strip():
        return version.strip()
    return None


def _read_mermaid_core_version(node_modules_dir: Path) -> str | None:
    candidates = [
        node_modules_dir / "mermaid" / "package.json",
        node_modules_dir / "@mermaid-js" / "mermaid-cli" / "node_modules" / "mermaid" / "package.json",
    ]
    for candidate in candidates:
        version = _read_package_version(candidate)
        if version:
            return version
    return None


def _find_workspace_root(start: Path) -> Path:
    resolved = start.resolve()
    for candidate in [resolved, *resolved.parents]:
        if (candidate / "nlplogix").exists():
            return candidate
    return resolved


def _find_nlplogix_root(workspace_root: Path) -> Path | None:
    candidate = workspace_root / "nlplogix"
    return candidate if candidate.exists() else None


def _find_manifest_version(nlplogix_root: Path | None) -> str | None:
    if nlplogix_root is None:
        return None
    manifest = _read_json(nlplogix_root / "syntax" / "SYNTAX_VERSION_MANIFEST.json")
    if not manifest:
        return None
    version = manifest.get("mermaid_version")
    if isinstance(version, str) and version.strip():
        return version.strip()
    return None


def _find_puppeteer_config(nlplogix_root: Path | None) -> str | None:
    if nlplogix_root is None:
        return None
    config_path = nlplogix_root / "scripts" / "puppeteer-config.json"
    if config_path.exists():
        return str(config_path)
    return None


def _local_renderer_info(nlplogix_root: Path | None, manifest_version: str | None) -> dict[str, Any]:
    if nlplogix_root is None:
        return {
            "available": False,
            "exact_match": False,
            "command": None,
            "mermaid_core_version": None,
            "source": "local-pinned-toolchain",
        }

    tool_root = nlplogix_root / "tools" / "mermaid-cli"
    command_candidates = [
        tool_root / "node_modules" / ".bin" / "mmdc.cmd",
        tool_root / "node_modules" / ".bin" / "mmdc",
    ]
    command_path = next((path for path in command_candidates if path.exists()), None)
    core_version = _read_mermaid_core_version(tool_root / "node_modules")
    exact_match = bool(command_path and (manifest_version is None or core_version == manifest_version))
    return {
        "available": command_path is not None,
        "exact_match": exact_match,
        "command": str(command_path) if command_path else None,
        "mermaid_core_version": core_version,
        "source": "local-pinned-toolchain",
    }


def _global_renderer_info(manifest_version: str | None) -> dict[str, Any]:
    mmdc_path = _command_path("mmdc")
    npm_path = _command_path("npm")
    core_version = None
    if mmdc_path and npm_path:
        rc, stdout, _ = _run_command([npm_path, "root", "-g"])
        if rc == 0 and stdout:
            core_version = _read_mermaid_core_version(Path(stdout))
    exact_match = bool(mmdc_path and (manifest_version is None or core_version == manifest_version))
    return {
        "available": mmdc_path is not None,
        "exact_match": exact_match,
        "command": mmdc_path,
        "mermaid_core_version": core_version,
        "source": "global-mmdc",
    }


def _resolver_module(nlplogix_root: Path | None) -> Any | None:
    if nlplogix_root is None:
        return None
    resolver_path = nlplogix_root / "scripts" / "mermaid_cli_resolver.py"
    if not resolver_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("workspace_mermaid_cli_resolver", resolver_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


def _resolve_renderer(
    nlplogix_root: Path | None,
    manifest_version: str | None,
    commands: dict[str, str | None],
) -> dict[str, Any]:
    package_spec = (
        f"@mermaid-js/mermaid-cli@{manifest_version}"
        if manifest_version
        else "@mermaid-js/mermaid-cli"
    )
    puppeteer_config_path = _find_puppeteer_config(nlplogix_root)

    workspace_resolver = _resolver_module(nlplogix_root)
    if workspace_resolver is not None:
        try:
            command = workspace_resolver.build_mermaid_cli_command(["--version"])
            executable = command[0]
            argument_prefix = command[1:-1]
            rc, _, _ = _run_command(command, timeout=15)
            if rc == 0:
                return {
                    "available": True,
                    "exact_match": True,
                    "source": "workspace-resolver",
                    "executable": executable,
                    "argument_prefix": argument_prefix,
                    "package_spec": package_spec,
                    "renderer_version": manifest_version or DEFAULT_MERMAID_VERSION,
                    "mermaid_version": manifest_version or DEFAULT_MERMAID_VERSION,
                    "puppeteer_config_path": puppeteer_config_path,
                    "install_command": DEFAULT_INSTALL_COMMAND,
                    "message": "Workspace Mermaid resolver is available",
                }
        except Exception:
            pass

    local_info = _local_renderer_info(nlplogix_root, manifest_version)
    if local_info["available"] and local_info["exact_match"]:
        return {
            "available": True,
            "exact_match": True,
            "source": local_info["source"],
            "executable": local_info["command"],
            "argument_prefix": [],
            "package_spec": package_spec,
            "renderer_version": local_info["mermaid_core_version"],
            "mermaid_version": manifest_version or local_info["mermaid_core_version"] or DEFAULT_MERMAID_VERSION,
            "puppeteer_config_path": puppeteer_config_path,
            "install_command": DEFAULT_INSTALL_COMMAND,
            "message": "Local pinned Mermaid toolchain matches the syntax manifest",
        }

    global_info = _global_renderer_info(manifest_version)
    if global_info["available"] and global_info["exact_match"]:
        return {
            "available": True,
            "exact_match": True,
            "source": global_info["source"],
            "executable": global_info["command"],
            "argument_prefix": [],
            "package_spec": package_spec,
            "renderer_version": global_info["mermaid_core_version"],
            "mermaid_version": manifest_version or global_info["mermaid_core_version"] or DEFAULT_MERMAID_VERSION,
            "puppeteer_config_path": puppeteer_config_path,
            "install_command": DEFAULT_INSTALL_COMMAND,
            "message": "Global mmdc matches the syntax manifest",
        }

    if commands["npx"] and manifest_version is None:
        return {
            "available": True,
            "exact_match": False,
            "source": "npx-unpinned",
            "executable": commands["npx"],
            "argument_prefix": ["--yes", "@mermaid-js/mermaid-cli"],
            "package_spec": package_spec,
            "renderer_version": None,
            "mermaid_version": DEFAULT_MERMAID_VERSION,
            "puppeteer_config_path": puppeteer_config_path,
            "install_command": DEFAULT_INSTALL_COMMAND,
            "message": "Using unpinned npx Mermaid CLI because no syntax manifest was found",
        }

    if global_info["available"] and global_info["mermaid_core_version"] and manifest_version:
        message = (
            f"Global mmdc uses Mermaid {global_info['mermaid_core_version']} but the syntax manifest "
            f"requires {manifest_version}. Install the local pinned toolchain with: {DEFAULT_INSTALL_COMMAND}"
        )
    else:
        message = (
            "No exact-match Mermaid renderer is available. "
            f"Install the local pinned toolchain with: {DEFAULT_INSTALL_COMMAND}"
        )

    return {
        "available": False,
        "exact_match": False,
        "source": "unavailable",
        "executable": None,
        "argument_prefix": [],
        "package_spec": package_spec,
        "renderer_version": None,
        "mermaid_version": manifest_version or DEFAULT_MERMAID_VERSION,
        "puppeteer_config_path": puppeteer_config_path,
        "install_command": DEFAULT_INSTALL_COMMAND,
        "message": message,
    }


def _detect_playwright() -> dict[str, Any]:
    python_available = False
    version = None
    try:
        import playwright  # type: ignore

        python_available = True
        version = getattr(playwright, "__version__", None)
    except Exception:
        python_available = False

    chromium_cache_path = None
    for candidate in PLAYWRIGHT_CACHE_CANDIDATES:
        if not str(candidate):
            continue
        if candidate.exists():
            chromium_dir = next((path for path in candidate.iterdir() if path.name.startswith("chromium")), None)
            if chromium_dir is not None:
                chromium_cache_path = str(chromium_dir)
                break

    chromium_on_path = next((path for name in CHROMIUM_COMMANDS if (path := _command_path(name))), None)
    browser_available = chromium_cache_path is not None or chromium_on_path is not None

    return {
        "python_available": python_available,
        "version": version,
        "browser_available": browser_available,
        "chromium_cache_path": chromium_cache_path,
        "chromium_on_path": chromium_on_path,
    }


def _detect_llm_repair(
    workspace_root: Path,
    *,
    env_file: str | Path | None = None,
    project_json: str | Path | None = None,
) -> dict[str, Any]:
    config = llm_config.load_workspace_llm_config(
        workspace_root,
        env_file=env_file,
        project_json=project_json,
    )
    openai_available = bool(config["openai_api_key"])
    azure_available = bool(config["azure_endpoint"] and config["azure_api_key"])
    default_provider = config["provider"]
    return {
        "available": openai_available or azure_available,
        "api_key_available": openai_available or azure_available,
        "providers": {
            "openai": openai_available,
            "azure-openai": azure_available,
        },
        "default_provider": default_provider,
        "default_model": DEFAULT_LLM_MODEL,
        "env_file_path": config["env_file_path"],
        "project_json_path": config["project_json_path"],
        "project_json_notice": config["project_json_notice"],
    }


def inspect_environment(
    workspace_root: str | Path | None = None,
    *,
    env_file: str | Path | None = None,
    project_json: str | Path | None = None,
) -> dict[str, Any]:
    start_path = Path(workspace_root or Path.cwd())
    resolved_workspace_root = _find_workspace_root(start_path)
    nlplogix_root = _find_nlplogix_root(resolved_workspace_root)
    commands = {
        "python3": _command_path("python3"),
        "node": _command_path("node"),
        "npm": _command_path("npm"),
        "npx": _command_path("npx"),
    }
    manifest_version = _find_manifest_version(nlplogix_root)
    renderer = _resolve_renderer(nlplogix_root, manifest_version, commands)
    playwright = _detect_playwright()
    llm = _detect_llm_repair(
        resolved_workspace_root,
        env_file=env_file,
        project_json=project_json,
    )

    syntax_available = commands["python3"] is not None
    render_available = syntax_available and commands["node"] is not None and renderer["available"]
    closed_loop_available = render_available and playwright["python_available"] and playwright["browser_available"]

    blocker = None
    next_step = None
    if commands["python3"] is None:
        blocker = "python3 is not available"
        next_step = "Install Python 3"
    elif commands["node"] is None:
        blocker = "node is not available"
        next_step = "Install Node.js"
    elif not renderer["available"]:
        blocker = renderer["message"]
        next_step = renderer["install_command"]
    elif not playwright["python_available"]:
        blocker = "Python Playwright is not installed"
        next_step = "python3 -m pip install playwright"
    elif not playwright["browser_available"]:
        blocker = "Playwright Chromium is not installed"
        next_step = "python3 -m playwright install chromium"

    return {
        "workspace_root": str(resolved_workspace_root),
        "nlplogix_root": str(nlplogix_root) if nlplogix_root else None,
        "manifest_version": manifest_version,
        "commands": commands,
        "renderer": renderer,
        "playwright": playwright,
        "llm": llm,
        "modes": {
            "syntax": syntax_available,
            "render": render_available,
            "closed_loop": closed_loop_available,
        },
        "blocker": blocker,
        "next_step": next_step,
        "platform": platform.platform(),
    }


def build_renderer_command(environment: dict[str, Any], args: list[str]) -> list[str]:
    renderer = environment["renderer"]
    if not renderer["available"] or not renderer["executable"]:
        raise RuntimeError(renderer["message"])
    return [renderer["executable"], *renderer["argument_prefix"], *args]


def _text_summary(environment: dict[str, Any]) -> str:
    renderer = environment["renderer"]
    lines = [
        "Mermaid Environment",
        f"  Workspace     : {environment['workspace_root']}",
        f"  Manifest      : {environment['manifest_version'] or 'not found'}",
        f"  Renderer      : {'available' if renderer['available'] else 'unavailable'}",
        f"  Source        : {renderer['source']}",
        f"  Mermaid core  : {renderer['renderer_version'] or 'unknown'}",
        f"  Syntax mode   : {'available' if environment['modes']['syntax'] else 'unavailable'}",
        f"  Render mode   : {'available' if environment['modes']['render'] else 'unavailable'}",
        f"  Closed-loop   : {'available' if environment['modes']['closed_loop'] else 'unavailable'}",
        (
            "  LLM repair    : "
            + (
                f"available ({environment['llm']['default_provider']})"
                if environment["llm"]["available"] and environment["llm"]["default_provider"]
                else "available"
                if environment["llm"]["available"]
                else "unavailable"
            )
        ),
    ]
    if environment["blocker"]:
        lines.append(f"  Blocker       : {environment['blocker']}")
    if environment["next_step"]:
        lines.append(f"  Next step     : {environment['next_step']}")
    if environment["llm"]["env_file_path"]:
        lines.append(f"  LLM env file  : {environment['llm']['env_file_path']}")
    if environment["llm"]["project_json_path"]:
        lines.append(f"  LLM project   : {environment['llm']['project_json_path']}")
    if environment["llm"]["project_json_notice"]:
        lines.append(f"  LLM note      : {environment['llm']['project_json_notice']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Mermaid skill environment")
    parser.add_argument(
        "--workspace-root",
        default=str(Path.cwd()),
        help="Workspace root or any path inside the workspace",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional .env.mermaid.local path. Defaults to <workspace>/.env.mermaid.local when present",
    )
    parser.add_argument(
        "--project-json",
        default=None,
        help="Optional project.json path. Defaults to <workspace>/project.json or a single nlplogix/*/*/project.json",
    )
    args = parser.parse_args()

    environment = inspect_environment(
        args.workspace_root,
        env_file=args.env_file,
        project_json=args.project_json,
    )
    if args.format == "json":
        print(json.dumps(environment, indent=2))
    else:
        print(_text_summary(environment))

    return 0 if environment["modes"]["syntax"] else 1


if __name__ == "__main__":
    sys.exit(main())
