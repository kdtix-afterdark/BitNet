#!/usr/bin/env python3
"""
Interactive Azure OpenAI setup for the Mermaid skill.

This script prompts for Azure OpenAI values, optionally validates them with a
small chat-completions call, and then emits shell exports or writes them to a
file. It cannot mutate the parent shell directly.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

try:
    from getpass import getpass
except ImportError:  # pragma: no cover
    getpass = None  # type: ignore[assignment]


DEFAULT_API_VERSION = "2024-05-01-preview"
DEFAULT_TEST_PROMPT = "Reply with OK."


@dataclass
class AzureOpenAIConfig:
    endpoint: str
    api_key: str
    deployment: str
    api_version: str


def _stderr(message: str = "", *, end: str = "\n") -> None:
    print(message, end=end, file=sys.stderr, flush=True)


def _read_line(prompt: str) -> str:
    _stderr(prompt, end="")
    value = sys.stdin.readline()
    if value == "":
        raise EOFError("stdin closed while waiting for input")
    return value.rstrip("\n")


def _prompt_value(label: str, default: str | None = None, *, secret: bool = False) -> str:
    prompt = f"{label}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    while True:
        if secret:
            if getpass is None:
                value = _read_line(prompt)
            else:
                value = getpass(prompt, stream=sys.stderr)
        else:
            value = _read_line(prompt)
        value = value.strip()
        if value:
            return value
        if default is not None:
            return default
        _stderr("Value required.")


def _infer_deployment(endpoint: str) -> str | None:
    match = re.search(r"/deployments/([^/?]+)", endpoint)
    if not match:
        return None
    return match.group(1)


def _normalize_endpoint(endpoint: str, api_version: str) -> str:
    endpoint = endpoint.strip()
    if endpoint and "api-version=" not in endpoint:
        separator = "&" if "?" in endpoint else "?"
        endpoint = f"{endpoint}{separator}api-version={api_version}"
    return endpoint


def _collect_config(args: argparse.Namespace) -> AzureOpenAIConfig:
    interactive = sys.stdin.isatty() and not args.non_interactive

    endpoint_default = args.endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment_default = (
        args.deployment
        or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        or (_infer_deployment(endpoint_default) if endpoint_default else None)
    )
    api_version_default = args.api_version or os.environ.get("AZURE_OPENAI_API_VERSION") or DEFAULT_API_VERSION
    api_key_default = args.api_key or os.environ.get("AZURE_OPENAI_API_KEY")

    if interactive:
        _stderr("Azure OpenAI setup for the Mermaid skill")
        _stderr("Press Enter to keep an existing value shown in brackets.")
        endpoint = _prompt_value("Endpoint", endpoint_default)
        deployment = _prompt_value("Deployment", deployment_default or _infer_deployment(endpoint))
        api_version = _prompt_value("API version", api_version_default)
        api_key = _prompt_value("API key", api_key_default, secret=True)
    else:
        endpoint = endpoint_default or ""
        deployment = deployment_default or ""
        api_version = api_version_default
        api_key = api_key_default or ""

    if not endpoint:
        raise ValueError("Azure OpenAI endpoint is required")
    if not deployment:
        raise ValueError("Azure OpenAI deployment is required")
    if not api_key:
        raise ValueError("Azure OpenAI API key is required")

    return AzureOpenAIConfig(
        endpoint=_normalize_endpoint(endpoint, api_version),
        api_key=api_key,
        deployment=deployment,
        api_version=api_version,
    )


def _validate_config(config: AzureOpenAIConfig, test_prompt: str) -> tuple[bool, str]:
    payload = {
        "messages": [{"role": "user", "content": test_prompt}],
        "max_completion_tokens": 20,
        "temperature": 0.0,
    }
    request = urllib_request.Request(
        config.endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "api-key": config.api_key,
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return False, f"HTTP {exc.code}: {detail[:500]}"
    except urllib_error.URLError as exc:
        return False, f"network error: {exc.reason}"
    except Exception as exc:  # pragma: no cover
        return False, f"{type(exc).__name__}: {exc}"

    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    if not isinstance(content, str) or not content.strip():
        return False, "Azure OpenAI returned an empty response"
    return True, content.strip()


def _shell_exports(config: AzureOpenAIConfig) -> str:
    return "\n".join(
        [
            f"export AZURE_OPENAI_ENDPOINT={shlex.quote(config.endpoint)}",
            f"export AZURE_OPENAI_API_KEY={shlex.quote(config.api_key)}",
            f"export AZURE_OPENAI_DEPLOYMENT={shlex.quote(config.deployment)}",
            f"export AZURE_OPENAI_API_VERSION={shlex.quote(config.api_version)}",
        ]
    )


def _powershell_exports(config: AzureOpenAIConfig) -> str:
    def quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    return "\n".join(
        [
            f"$env:AZURE_OPENAI_ENDPOINT = {quote(config.endpoint)}",
            f"$env:AZURE_OPENAI_API_KEY = {quote(config.api_key)}",
            f"$env:AZURE_OPENAI_DEPLOYMENT = {quote(config.deployment)}",
            f"$env:AZURE_OPENAI_API_VERSION = {quote(config.api_version)}",
        ]
    )


def _dotenv_exports(config: AzureOpenAIConfig) -> str:
    return "\n".join(
        [
            f"AZURE_OPENAI_ENDPOINT={json.dumps(config.endpoint)}",
            f"AZURE_OPENAI_API_KEY={json.dumps(config.api_key)}",
            f"AZURE_OPENAI_DEPLOYMENT={json.dumps(config.deployment)}",
            f"AZURE_OPENAI_API_VERSION={json.dumps(config.api_version)}",
        ]
    )


def _json_output(config: AzureOpenAIConfig) -> str:
    return json.dumps(
        {
            "AZURE_OPENAI_ENDPOINT": config.endpoint,
            "AZURE_OPENAI_API_KEY": config.api_key,
            "AZURE_OPENAI_DEPLOYMENT": config.deployment,
            "AZURE_OPENAI_API_VERSION": config.api_version,
        },
        indent=2,
    )


def _render_output(config: AzureOpenAIConfig, output_format: str, validation: str) -> str:
    if output_format == "shell":
        return _shell_exports(config)
    if output_format == "powershell":
        return _powershell_exports(config)
    if output_format == "dotenv":
        return _dotenv_exports(config)
    if output_format == "json":
        return _json_output(config)

    return "\n".join(
        [
            "Azure OpenAI Mermaid setup complete.",
            f"Validation: {validation}",
            "",
            "Export for zsh/bash:",
            _shell_exports(config),
        ]
    )


def _write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive Azure OpenAI env setup for the Mermaid skill")
    parser.add_argument("--endpoint", default=None, help="Azure OpenAI chat completions endpoint")
    parser.add_argument("--api-key", default=None, help="Azure OpenAI API key")
    parser.add_argument("--deployment", default=None, help="Azure OpenAI deployment name")
    parser.add_argument("--api-version", default=None, help="Azure OpenAI API version")
    parser.add_argument(
        "--format",
        choices=["text", "shell", "powershell", "dotenv", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--write-file", default=None, help="Optional file path to write the rendered output")
    parser.add_argument("--no-validate", action="store_true", help="Skip the Azure OpenAI test call")
    parser.add_argument("--non-interactive", action="store_true", help="Do not prompt; require args or env vars")
    parser.add_argument("--test-prompt", default=DEFAULT_TEST_PROMPT, help="Validation prompt text")
    args = parser.parse_args()

    try:
        config = _collect_config(args)
    except (ValueError, EOFError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    validation_status = "skipped"
    if not args.no_validate:
        ok, message = _validate_config(config, args.test_prompt)
        validation_status = f"passed ({message})" if ok else f"failed ({message})"
        if not ok:
            print(f"Validation failed: {message}", file=sys.stderr)
            return 1

    output = _render_output(config, args.format, validation_status)
    if args.write_file:
        output_path = Path(args.write_file).expanduser()
        _write_output(output_path, output)
        if args.format == "text":
            print(output)
            print(f"\nWrote setup output to {output_path}")
        else:
            print(f"Wrote {args.format} output to {output_path}")
        return 0

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
