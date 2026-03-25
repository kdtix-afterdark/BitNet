#!/usr/bin/env python3
"""
Skill-owned Mermaid closed-loop runner.

This first-pass runner stays Mermaid-only. It discovers Mermaid diagrams,
resolves the exact renderer for the active workspace, renders themed light and
dark variants, applies deterministic readability fixes, writes a comparison
gallery, and records a report describing the chosen pass for each diagram.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Iterable
from urllib import error as urllib_error
from urllib import request as urllib_request

import check_env
import llm_config

LIGHT_INIT = (
    '%%{init: {"theme":"base","themeVariables":{'
    '"fontFamily":"Tahoma,Arial,sans-serif",'
    '"background":"#FFFFFF",'
    '"titleColor":"#6FBE44",'
    '"textColor":"#3C3C3C",'
    '"lineColor":"#666766",'
    '"defaultLinkColor":"#666766",'
    '"edgeLabelBackground":"#FFFFFF",'
    '"primaryColor":"#E4EBF5",'
    '"primaryTextColor":"#3C3C3C",'
    '"primaryBorderColor":"#6FBE44",'
    '"secondaryColor":"#D0E6F5",'
    '"secondaryTextColor":"#313C41",'
    '"secondaryBorderColor":"#05A48E",'
    '"tertiaryColor":"#DDEFFC",'
    '"tertiaryTextColor":"#313C41",'
    '"tertiaryBorderColor":"#357CF6",'
    '"mainBkg":"#E4EBF5",'
    '"secondBkg":"#D0E6F5",'
    '"tertiaryBkg":"#DDEFFC",'
    '"nodeBorder":"#6FBE44",'
    '"clusterBkg":"#EEF3F8",'
    '"clusterBorder":"#666766",'
    '"labelTextColor":"#3C3C3C",'
    '"loopTextColor":"#3C3C3C",'
    '"noteBkgColor":"#FEFCE8",'
    '"noteTextColor":"#3C3C3C",'
    '"noteBorderColor":"#6FBE44",'
    '"activationBkgColor":"#D0E6F5",'
    '"activationBorderColor":"#357CF6",'
    '"actorBkg":"#E4EBF5",'
    '"actorBorder":"#6FBE44",'
    '"actorTextColor":"#3C3C3C",'
    '"actorLineColor":"#666766",'
    '"signalColor":"#666766",'
    '"signalTextColor":"#3C3C3C",'
    '"fillType0":"#E4EBF5","fillType1":"#D0E6F5","fillType2":"#DDEFFC",'
    '"cScale0":"#6FBE44","cScaleLabel0":"#FFFFFF",'
    '"cScale1":"#05A48E","cScaleLabel1":"#FFFFFF",'
    '"cScale2":"#357CF6","cScaleLabel2":"#FFFFFF",'
    '"cScale3":"#666766","cScaleLabel3":"#FFFFFF",'
    '"cScale4":"#2C4A28","cScaleLabel4":"#FFFFFF",'
    '"git0":"#6FBE44","git1":"#05A48E","git2":"#357CF6","git3":"#666766",'
    '"gitBranchLabel0":"#FFFFFF","gitBranchLabel1":"#FFFFFF",'
    '"gitBranchLabel2":"#FFFFFF","gitBranchLabel3":"#FFFFFF",'
    '"attributeBackgroundColorEven":"#E4EBF5",'
    '"attributeBackgroundColorOdd":"#D0E6F5"'
    '}}}%%'
)

DARK_INIT = (
    '%%{init: {"theme":"base","themeVariables":{'
    '"fontFamily":"Tahoma,Arial,sans-serif",'
    '"background":"#3C3C3C",'
    '"titleColor":"#6FBE44",'
    '"textColor":"#F7F9FF",'
    '"lineColor":"#D9D9D9",'
    '"defaultLinkColor":"#D9D9D9",'
    '"edgeLabelBackground":"#253A45",'
    '"primaryColor":"#1E3A4A",'
    '"primaryTextColor":"#F7F9FF",'
    '"primaryBorderColor":"#6FBE44",'
    '"secondaryColor":"#022918",'
    '"secondaryTextColor":"#F7F9FF",'
    '"secondaryBorderColor":"#05A48E",'
    '"tertiaryColor":"#012D57",'
    '"tertiaryTextColor":"#F7F9FF",'
    '"tertiaryBorderColor":"#357CF6",'
    '"mainBkg":"#1E3A4A",'
    '"secondBkg":"#022918",'
    '"tertiaryBkg":"#012D57",'
    '"nodeBorder":"#6FBE44",'
    '"clusterBkg":"#253A45",'
    '"clusterBorder":"#6FBE44",'
    '"labelTextColor":"#F7F9FF",'
    '"loopTextColor":"#F7F9FF",'
    '"noteBkgColor":"#022918",'
    '"noteTextColor":"#F7F9FF",'
    '"noteBorderColor":"#05A48E",'
    '"activationBkgColor":"#012D57",'
    '"activationBorderColor":"#357CF6",'
    '"actorBkg":"#1E3A4A",'
    '"actorBorder":"#6FBE44",'
    '"actorTextColor":"#F7F9FF",'
    '"actorLineColor":"#D9D9D9",'
    '"signalColor":"#D9D9D9",'
    '"signalTextColor":"#F7F9FF",'
    '"fillType0":"#1E3A4A","fillType1":"#022918","fillType2":"#012D57",'
    '"cScale0":"#6FBE44","cScaleLabel0":"#000000",'
    '"cScale1":"#05A48E","cScaleLabel1":"#FFFFFF",'
    '"cScale2":"#357CF6","cScaleLabel2":"#FFFFFF",'
    '"cScale3":"#888688","cScaleLabel3":"#FFFFFF",'
    '"cScale4":"#2C4A28","cScaleLabel4":"#FFFFFF",'
    '"git0":"#6FBE44","git1":"#05A48E","git2":"#357CF6","git3":"#888688",'
    '"gitBranchLabel0":"#000000","gitBranchLabel1":"#FFFFFF",'
    '"gitBranchLabel2":"#FFFFFF","gitBranchLabel3":"#FFFFFF",'
    '"attributeBackgroundColorEven":"#1E3A4A",'
    '"attributeBackgroundColorOdd":"#022918"'
    '}}}%%'
)

LIGHT_CLASSDEF = "classDef default fill:#E4EBF5,stroke:#6FBE44,color:#3C3C3C,stroke-width:1.5px;"
DARK_CLASSDEF = "classDef default fill:#1E3A4A,stroke:#6FBE44,color:#F7F9FF,stroke-width:1.5px;"
LIGHT_BG = "#FFFFFF"
DARK_BG = "#3C3C3C"

LIGHT_ER_CSS = """
.row-rect-even > path:first-child { fill: #D0DFF0 !important; }
.row-rect-odd > path:first-child  { fill: #E4EBF5 !important; }
"""

DARK_ER_CSS = """
.row-rect-odd > path:first-child  { fill: #253A45 !important; }
.row-rect-even > path:first-child { fill: #1E3A4A !important; }
"""

DARK_C4_CSS = """
[stroke="#444444"] { stroke: #D9D9D9 !important; }
[stroke="#000000"] { stroke: #D9D9D9 !important; }
[fill="black"] { fill: #D9D9D9 !important; }
"""

LLM_API_URL = "https://api.openai.com/v1/responses"
MAX_SYNTAX_REFERENCE_CHARS = 6000
LLM_REPAIR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "patched_mermaid": {"type": "string"},
        "summary": {"type": "string"},
        "applied_fixes": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["patched_mermaid", "summary", "applied_fixes"],
}


@dataclass
class DiagramInput:
    stem: str
    origin: str
    source: str
    diagram_type: str


@dataclass
class VariantOutput:
    source_path: str | None
    light_svg: str | None
    dark_svg: str | None
    light_ok: bool
    dark_ok: bool
    light_error: str | None = None
    dark_error: str | None = None


@dataclass
class PassResult:
    pass_index: int
    source_variant: str
    strategy: str
    score: int
    applied_fixes: list[str]
    notes: list[str]
    outputs: VariantOutput


@dataclass
class LLMRepairAttempt:
    enabled: bool
    attempted: bool
    accepted: bool
    provider: str | None
    model: str | None
    reason: str | None
    baseline_score: int | None
    candidate_score: int | None
    request_path: str | None
    response_path: str | None
    candidate_path: str | None
    notes: list[str]


@dataclass
class LLMSettings:
    provider: str
    model: str
    available: bool
    api_key: str | None = None
    azure_endpoint: str | None = None
    azure_deployment: str | None = None
    azure_api_version: str | None = None
    env_file_path: str | None = None
    project_json_path: str | None = None
    project_json_notice: str | None = None


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "diagram"


def _strip_existing_init(source: str) -> str:
    return re.sub(r"^%%\{[^%]+\}%%\s*\n?", "", source, flags=re.MULTILINE | re.DOTALL).strip()


def _strip_markdown_fences(source: str) -> str:
    match = re.fullmatch(r"```(?:mermaid)?\s*(.*?)```", source.strip(), flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return source.strip()


def _inject_classdef(source: str, classdef: str) -> str:
    stripped = source.strip()
    if not re.match(r"\s*(flowchart|graph)\s+", stripped, re.IGNORECASE):
        return source
    if re.search(r"^\s*classDef\s+default\b", stripped, flags=re.IGNORECASE | re.MULTILINE):
        return source
    lines = stripped.splitlines()
    if len(lines) == 1:
        return f"{lines[0]}\n    {classdef}"
    return lines[0] + "\n    " + classdef + "\n" + "\n".join(lines[1:])


def _detect_diagram_type(source: str) -> str:
    patterns = [
        ("flowchart", r"^(flowchart|graph)\b"),
        ("sequence", r"^sequenceDiagram\b"),
        ("class", r"^classDiagram\b"),
        ("er", r"^erDiagram\b"),
        ("gantt", r"^gantt\b"),
        ("pie", r"^pie\b"),
        ("state", r"^stateDiagram"),
        ("gitgraph", r"^gitGraph\b"),
        ("journey", r"^journey\b"),
        ("timeline", r"^timeline\b"),
        ("xychart", r"^(xychart-beta|xyChart)\b"),
        ("quadrant", r"^quadrantChart\b"),
        ("architecture", r"^architecture-beta\b"),
        ("block", r"^block-beta\b"),
        ("packet", r"^packet-beta\b"),
        ("kanban", r"^kanban\b"),
        ("requirement", r"^requirementDiagram\b"),
        ("c4", r"^C4(Context|Container|Component|Dynamic|Deployment)\b"),
    ]
    in_init_block = False
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("%%{") and not line.endswith("}%%"):
            in_init_block = True
            continue
        if in_init_block:
            if "}%%" in line:
                in_init_block = False
            continue
        if line.startswith("%%") or line.startswith("---"):
            continue
        for diagram_type, pattern in patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return diagram_type
        break
    return "unknown"


def _extract_markdown_diagrams(path: Path) -> Iterable[DiagramInput]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
    rel = path.name
    for index, match in enumerate(pattern.finditer(text), start=1):
        source = match.group(1).strip()
        if not source:
            continue
        stem = _safe_stem(f"{path.stem}-mmd{index:02d}")
        yield DiagramInput(
            stem=stem,
            origin=f"{rel} block #{index}",
            source=source,
            diagram_type=_detect_diagram_type(source),
        )


def discover_diagrams(paths: list[Path], include_markdown: bool) -> list[DiagramInput]:
    diagrams: list[DiagramInput] = []
    seen: set[str] = set()
    for path in paths:
        if path.is_dir():
            for mmd in sorted(path.rglob("*.mmd")):
                key = str(mmd.resolve())
                if key in seen:
                    continue
                seen.add(key)
                source = mmd.read_text(encoding="utf-8").strip()
                diagrams.append(
                    DiagramInput(
                        stem=_safe_stem(str(mmd.relative_to(path))),
                        origin=str(mmd),
                        source=source,
                        diagram_type=_detect_diagram_type(source),
                    )
                )
            if include_markdown:
                for markdown in sorted(path.rglob("*.md")):
                    for diagram in _extract_markdown_diagrams(markdown):
                        key = f"{markdown.resolve()}::{diagram.stem}"
                        if key in seen:
                            continue
                        seen.add(key)
                        diagrams.append(diagram)
            continue

        if path.suffix.lower() == ".mmd":
            source = path.read_text(encoding="utf-8").strip()
            diagrams.append(
                DiagramInput(
                    stem=_safe_stem(path.stem),
                    origin=str(path),
                    source=source,
                    diagram_type=_detect_diagram_type(source),
                )
            )
        elif include_markdown and path.suffix.lower() in {".md", ".markdown"}:
            diagrams.extend(_extract_markdown_diagrams(path))
    return diagrams


def _strategy_plan(diagram_type: str) -> list[dict[str, Any]]:
    plans = [
        {
            "name": "theme-only",
            "apply_classdef": False,
            "light_css": None,
            "dark_css": None,
            "fixes": ["theme-variables"],
        }
    ]
    if diagram_type == "flowchart":
        plans.append(
            {
                "name": "theme-plus-classdef",
                "apply_classdef": True,
                "light_css": None,
                "dark_css": None,
                "fixes": ["theme-variables", "flowchart-classdef"],
            }
        )
    elif diagram_type == "er":
        plans.append(
            {
                "name": "theme-plus-er-css",
                "apply_classdef": False,
                "light_css": LIGHT_ER_CSS,
                "dark_css": DARK_ER_CSS,
                "fixes": ["theme-variables", "er-css-overrides"],
            }
        )
    elif diagram_type == "c4":
        plans.append(
            {
                "name": "theme-plus-c4-dark-css",
                "apply_classdef": False,
                "light_css": None,
                "dark_css": DARK_C4_CSS,
                "fixes": ["theme-variables", "c4-dark-css-overrides"],
            }
        )
    return plans


def _build_variant_source(body: str, init_block: str, classdef: str | None) -> str:
    transformed = body
    if classdef:
        transformed = _inject_classdef(transformed, classdef)
    return init_block + "\n" + transformed.strip()


def _normalize_renderer_error(stdout: str, stderr: str, returncode: int, output_path: Path) -> str:
    text = "\n".join(part for part in (stderr.strip(), stdout.strip()) if part).strip()
    if not text:
        text = f"renderer exited with code {returncode} and did not create {output_path.name}"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    trimmed = "\n".join(lines[:8])
    return trimmed[:1400]


def _error_first_line(value: str | None) -> str | None:
    if not value:
        return None
    first_line = next((line.strip() for line in value.splitlines() if line.strip()), None)
    if not first_line:
        return None
    return first_line[:180]


def _load_syntax_reference(environment: dict[str, Any], diagram_type: str) -> str | None:
    if not diagram_type or diagram_type == "unknown":
        return None
    nlplogix_root = environment.get("nlplogix_root")
    if not nlplogix_root:
        return None
    reference_path = Path(nlplogix_root) / "syntax" / f"{diagram_type}.md"
    if not reference_path.exists():
        return None
    text = reference_path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    return text[:MAX_SYNTAX_REFERENCE_CHARS]


def _llm_pass_summaries(pass_results: list[PassResult]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for item in pass_results:
        summaries.append(
            {
                "source_variant": item.source_variant,
                "strategy": item.strategy,
                "score": item.score,
                "applied_fixes": item.applied_fixes,
                "notes": item.notes,
                "light_ok": item.outputs.light_ok,
                "dark_ok": item.outputs.dark_ok,
                "light_error": _error_first_line(item.outputs.light_error),
                "dark_error": _error_first_line(item.outputs.dark_error),
            }
        )
    return summaries


def _parse_json_text(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, flags=re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _extract_structured_output(response_data: dict[str, Any]) -> dict[str, Any] | None:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        parsed = _parse_json_text(output_text.strip())
        if parsed:
            return parsed

    for item in response_data.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            structured = content.get("json")
            if isinstance(structured, dict):
                return structured
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                parsed = _parse_json_text(text.strip())
                if parsed:
                    return parsed
    return None


def _post_responses_request(api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib_request.Request(
        LLM_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:800]}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc


def _normalize_azure_endpoint(endpoint: str, api_version: str | None) -> str:
    if not api_version or "api-version=" in endpoint:
        return endpoint
    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}api-version={api_version}"


def _post_azure_chat_request(endpoint: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib_request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:800]}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc


def _build_llm_prompts(
    diagram: DiagramInput,
    body: str,
    environment: dict[str, Any],
    baseline_passes: list[PassResult],
    best_result: PassResult,
    syntax_reference: str | None,
) -> tuple[str, str]:
    manifest_version = environment.get("manifest_version") or check_env.DEFAULT_MERMAID_VERSION
    system_prompt = (
        "You repair Mermaid diagram source. "
        "Return only a JSON object with keys patched_mermaid, summary, and applied_fixes. "
        "Preserve the diagram semantics. "
        "Do not wrap the Mermaid in Markdown fences. "
        "Do not add Mermaid init blocks because the caller injects themes separately. "
        "Use the smallest safe syntax or structure change needed to make the diagram render cleanly in Mermaid "
        f"{manifest_version}. "
        "Prefer syntax fixes, label cleanup, and layout-safe rewrites over stylistic churn."
    )
    user_prompt = "\n".join(
        [
            f"Diagram origin: {diagram.origin}",
            f"Detected type: {diagram.diagram_type}",
            f"Target Mermaid version: {manifest_version}",
            f"Baseline best score: {best_result.score}",
            "Baseline render evaluations:",
            json.dumps(_llm_pass_summaries(baseline_passes), indent=2),
            "Relevant syntax reference:",
            syntax_reference or "No syntax reference was available for this diagram type.",
            "Original Mermaid body:",
            body,
        ]
    )
    return system_prompt, user_prompt


def _build_openai_payload(model: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return {
        "model": model,
        "reasoning": {"effort": "medium"},
        "max_output_tokens": 2500,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "mermaid_repair",
                "strict": True,
                "schema": LLM_REPAIR_SCHEMA,
            }
        },
    }


def _build_azure_payload(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_completion_tokens": 2500,
        "temperature": 0.1,
    }


def _extract_azure_structured_output(response_data: dict[str, Any]) -> dict[str, Any] | None:
    choices = response_data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message", {})
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return _parse_json_text(content.strip())
    return None


def _resolve_llm_settings(args: argparse.Namespace, workspace_root: Path) -> LLMSettings:
    discovered = llm_config.load_workspace_llm_config(
        workspace_root,
        env_file=args.env_file,
        project_json=args.project_json,
    )
    provider = args.llm_provider
    openai_api_key = discovered["openai_api_key"]
    azure_endpoint = discovered["azure_endpoint"]
    azure_api_key = discovered["azure_api_key"]
    azure_deployment = discovered["azure_deployment"]
    azure_api_version = discovered["azure_api_version"]

    if args.azure_openai_endpoint:
        azure_endpoint = args.azure_openai_endpoint
    if args.azure_openai_api_key:
        azure_api_key = args.azure_openai_api_key
    if args.azure_openai_deployment:
        azure_deployment = args.azure_openai_deployment
    if args.azure_openai_api_version:
        azure_api_version = args.azure_openai_api_version

    if provider == "auto":
        if openai_api_key:
            provider = "openai"
        elif azure_endpoint and azure_api_key:
            provider = "azure-openai"
        else:
            provider = "openai"

    if provider == "azure-openai":
        return LLMSettings(
            provider=provider,
            model=azure_deployment or args.llm_model,
            available=bool(azure_endpoint and azure_api_key),
            api_key=azure_api_key,
            azure_endpoint=_normalize_azure_endpoint(azure_endpoint, azure_api_version) if azure_endpoint else None,
            azure_deployment=azure_deployment,
            azure_api_version=azure_api_version,
            env_file_path=discovered["env_file_path"],
            project_json_path=discovered["project_json_path"],
            project_json_notice=discovered["project_json_notice"],
        )

    return LLMSettings(
        provider="openai",
        model=args.llm_model,
        available=bool(openai_api_key),
        api_key=openai_api_key,
        env_file_path=discovered["env_file_path"],
        project_json_path=discovered["project_json_path"],
        project_json_notice=discovered["project_json_notice"],
    )


def _ensure_puppeteer_config(environment: dict[str, Any]) -> str:
    renderer = environment["renderer"]
    if renderer["puppeteer_config_path"]:
        return renderer["puppeteer_config_path"]
    temp_dir = Path(tempfile.gettempdir())
    config_path = temp_dir / "mermaid-skill-puppeteer.json"
    config_path.write_text(
        json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}, indent=2),
        encoding="utf-8",
    )
    return str(config_path)


def _render_svg(
    environment: dict[str, Any],
    source: str,
    output_path: Path,
    background: str,
    css_override: str | None,
) -> tuple[bool, str | None]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    puppeteer_config = _ensure_puppeteer_config(environment)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as handle:
        handle.write(source)
        temp_mmd = Path(handle.name)

    temp_css: Path | None = None
    try:
        if css_override:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".css", delete=False, encoding="utf-8") as css_handle:
                css_handle.write(css_override)
                temp_css = Path(css_handle.name)

        command = check_env.build_renderer_command(
            environment,
            [
                "-i", str(temp_mmd),
                "-o", str(output_path),
                "-e", "svg",
                "-b", background,
                "-w", "1920",
                "-H", "1080",
                "-p", puppeteer_config,
            ],
        )
        if temp_css:
            command.extend(["-C", str(temp_css)])
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
        success = result.returncode == 0 and output_path.exists()
        if success:
            return True, None
        return False, _normalize_renderer_error(result.stdout, result.stderr, result.returncode, output_path)
    finally:
        temp_mmd.unlink(missing_ok=True)
        if temp_css:
            temp_css.unlink(missing_ok=True)


def _score_pass(diagram_type: str, plan: dict[str, Any], light_ok: bool, dark_ok: bool) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []
    if light_ok:
        score += 40
    else:
        notes.append("light render failed")
    if dark_ok:
        score += 40
    else:
        notes.append("dark render failed")
    if plan["apply_classdef"] and diagram_type == "flowchart":
        score += 10
        notes.append("flowchart classDef applied")
    if plan["dark_css"] and diagram_type == "er":
        score += 10
        notes.append("erDiagram row CSS applied")
    if plan["dark_css"] and diagram_type == "c4":
        score += 10
        notes.append("C4 dark CSS applied")
    return score, notes


def _write_patch_files(body: str, best_result: PassResult, output_dir: Path) -> str | None:
    patched_source = body
    if "flowchart-classdef" in best_result.applied_fixes:
        patched_source = _inject_classdef(body, LIGHT_CLASSDEF)
    patch_path = output_dir / f"{output_dir.name}-suggested.mmd"
    patch_path.write_text(patched_source.strip() + "\n", encoding="utf-8")
    return str(patch_path)


def _evaluate_body(
    diagram: DiagramInput,
    body: str,
    environment: dict[str, Any],
    diagram_dir: Path,
    max_passes: int,
    source_variant: str,
    file_prefix: str,
) -> tuple[list[PassResult], PassResult]:
    plans = _strategy_plan(diagram.diagram_type)[:max_passes]
    pass_results: list[PassResult] = []

    for pass_index, plan in enumerate(plans, start=1):
        light_classdef = LIGHT_CLASSDEF if plan["apply_classdef"] else None
        dark_classdef = DARK_CLASSDEF if plan["apply_classdef"] else None
        light_source = _build_variant_source(body, LIGHT_INIT, light_classdef)
        dark_source = _build_variant_source(body, DARK_INIT, dark_classdef)

        light_svg = diagram_dir / f"{file_prefix}-{pass_index:02d}-light.svg"
        dark_svg = diagram_dir / f"{file_prefix}-{pass_index:02d}-dark.svg"
        light_ok, light_error = _render_svg(environment, light_source, light_svg, LIGHT_BG, plan["light_css"])
        dark_ok, dark_error = _render_svg(environment, dark_source, dark_svg, DARK_BG, plan["dark_css"])
        score, notes = _score_pass(diagram.diagram_type, plan, light_ok, dark_ok)
        if not light_ok and light_error:
            notes.append(f"light error: {_error_first_line(light_error)}")
        if not dark_ok and dark_error:
            notes.append(f"dark error: {_error_first_line(dark_error)}")

        pass_results.append(
            PassResult(
                pass_index=pass_index,
                source_variant=source_variant,
                strategy=plan["name"],
                score=score,
                applied_fixes=list(plan["fixes"]),
                notes=notes,
                outputs=VariantOutput(
                    source_path=None,
                    light_svg=str(light_svg) if light_ok else None,
                    dark_svg=str(dark_svg) if dark_ok else None,
                    light_ok=light_ok,
                    dark_ok=dark_ok,
                    light_error=light_error,
                    dark_error=dark_error,
                ),
            )
        )

    best_result = max(pass_results, key=lambda item: item.score)
    return pass_results, best_result


def _should_attempt_llm_repair(best_result: PassResult, threshold: int) -> bool:
    outputs = best_result.outputs
    if not outputs.light_ok or not outputs.dark_ok:
        return True
    return best_result.score < threshold


def _attempt_llm_repair(
    diagram: DiagramInput,
    body: str,
    environment: dict[str, Any],
    llm_settings: LLMSettings,
    baseline_passes: list[PassResult],
    baseline_best: PassResult,
    diagram_dir: Path,
    max_passes: int,
    enable_llm_repair: bool,
    llm_threshold: int,
) -> tuple[LLMRepairAttempt, DiagramInput | None, list[PassResult], PassResult | None]:
    attempt = LLMRepairAttempt(
        enabled=enable_llm_repair,
        attempted=False,
        accepted=False,
        provider=llm_settings.provider if enable_llm_repair else None,
        model=llm_settings.model if enable_llm_repair else None,
        reason=None,
        baseline_score=baseline_best.score,
        candidate_score=None,
        request_path=None,
        response_path=None,
        candidate_path=None,
        notes=[],
    )
    if not enable_llm_repair:
        attempt.reason = "LLM repair disabled"
        return attempt, None, [], None
    if not llm_settings.available or not llm_settings.api_key:
        if llm_settings.provider == "azure-openai":
            attempt.reason = "Azure OpenAI config is incomplete"
        else:
            attempt.reason = "OPENAI_API_KEY not set"
        if llm_settings.project_json_notice:
            attempt.notes.append(llm_settings.project_json_notice)
        return attempt, None, [], None
    if not _should_attempt_llm_repair(baseline_best, llm_threshold):
        attempt.reason = f"baseline score {baseline_best.score} meets threshold {llm_threshold}"
        return attempt, None, [], None

    attempt.attempted = True
    syntax_reference = _load_syntax_reference(environment, diagram.diagram_type)
    if syntax_reference:
        attempt.notes.append("syntax reference included")

    system_prompt, user_prompt = _build_llm_prompts(
        diagram=diagram,
        body=body,
        environment=environment,
        baseline_passes=baseline_passes,
        best_result=baseline_best,
        syntax_reference=syntax_reference,
    )
    if llm_settings.provider == "azure-openai":
        payload = _build_azure_payload(system_prompt, user_prompt)
        request_record = {
            "provider": llm_settings.provider,
            "model": llm_settings.model,
            "deployment": llm_settings.azure_deployment,
            "endpoint": llm_settings.azure_endpoint,
            "api_version": llm_settings.azure_api_version,
            "payload": payload,
        }
    else:
        payload = _build_openai_payload(llm_settings.model, system_prompt, user_prompt)
        request_record = {
            "provider": llm_settings.provider,
            "model": llm_settings.model,
            "payload": payload,
        }
    request_path = diagram_dir / "llm-request.json"
    response_path = diagram_dir / "llm-response.json"
    request_path.write_text(json.dumps(request_record, indent=2), encoding="utf-8")
    attempt.request_path = str(request_path)
    attempt.response_path = str(response_path)

    try:
        if llm_settings.provider == "azure-openai":
            if not llm_settings.azure_endpoint:
                attempt.reason = "Azure OpenAI endpoint is missing"
                return attempt, None, [], None
            response_data = _post_azure_chat_request(
                llm_settings.azure_endpoint,
                llm_settings.api_key,
                payload,
            )
        else:
            response_data = _post_responses_request(llm_settings.api_key, payload)
        response_path.write_text(json.dumps(response_data, indent=2), encoding="utf-8")
    except Exception as exc:
        response_path.write_text(json.dumps({"error": str(exc)}, indent=2), encoding="utf-8")
        attempt.reason = f"LLM request failed: {exc}"
        return attempt, None, [], None

    structured = (
        _extract_azure_structured_output(response_data)
        if llm_settings.provider == "azure-openai"
        else _extract_structured_output(response_data)
    )
    if not structured:
        attempt.reason = "LLM response did not contain parseable structured output"
        return attempt, None, [], None

    patched_mermaid = structured.get("patched_mermaid")
    if not isinstance(patched_mermaid, str) or not patched_mermaid.strip():
        attempt.reason = "LLM returned an empty patched_mermaid value"
        return attempt, None, [], None

    patched_body = _strip_existing_init(_strip_markdown_fences(patched_mermaid))
    if not patched_body:
        attempt.reason = "LLM candidate was empty after removing fences and init blocks"
        return attempt, None, [], None

    summary = structured.get("summary")
    if isinstance(summary, str) and summary.strip():
        attempt.notes.append(summary.strip())
    applied_fixes = structured.get("applied_fixes")
    if isinstance(applied_fixes, list):
        attempt.notes.extend(str(item).strip() for item in applied_fixes if str(item).strip())

    candidate_path = diagram_dir / "llm-candidate.mmd"
    candidate_path.write_text(patched_body.strip() + "\n", encoding="utf-8")
    attempt.candidate_path = str(candidate_path)

    candidate_diagram = DiagramInput(
        stem=diagram.stem,
        origin=diagram.origin,
        source=patched_body,
        diagram_type=_detect_diagram_type(patched_body),
    )
    candidate_passes, candidate_best = _evaluate_body(
        diagram=candidate_diagram,
        body=patched_body,
        environment=environment,
        diagram_dir=diagram_dir,
        max_passes=max_passes,
        source_variant="llm-repair",
        file_prefix="llm-pass",
    )
    attempt.candidate_score = candidate_best.score
    if candidate_best.score > baseline_best.score:
        attempt.accepted = True
        attempt.reason = "LLM candidate improved the render score"
    else:
        attempt.reason = "LLM candidate did not improve the render score"
    return attempt, candidate_diagram, candidate_passes, candidate_best


def iterate_diagram(
    diagram: DiagramInput,
    environment: dict[str, Any],
    llm_settings: LLMSettings,
    output_dir: Path,
    max_passes: int,
    write_patches: bool,
    enable_llm_repair: bool,
    llm_threshold: int,
) -> dict[str, Any]:
    diagram_dir = output_dir / diagram.stem
    diagram_dir.mkdir(parents=True, exist_ok=True)
    body = _strip_existing_init(diagram.source)
    baseline_passes, baseline_best = _evaluate_body(
        diagram=diagram,
        body=body,
        environment=environment,
        diagram_dir=diagram_dir,
        max_passes=max_passes,
        source_variant="baseline",
        file_prefix="pass",
    )
    llm_repair, candidate_diagram, candidate_passes, candidate_best = _attempt_llm_repair(
        diagram=diagram,
        body=body,
        environment=environment,
        llm_settings=llm_settings,
        baseline_passes=baseline_passes,
        baseline_best=baseline_best,
        diagram_dir=diagram_dir,
        max_passes=max_passes,
        enable_llm_repair=enable_llm_repair,
        llm_threshold=llm_threshold,
    )

    best_result = baseline_best
    best_body = body
    final_diagram_type = diagram.diagram_type
    pass_results = list(baseline_passes)
    if candidate_passes:
        pass_results.extend(candidate_passes)
    if llm_repair.accepted and candidate_diagram and candidate_best:
        best_result = candidate_best
        best_body = candidate_diagram.source
        final_diagram_type = candidate_diagram.diagram_type

    patch_path = _write_patch_files(best_body, best_result, diagram_dir) if write_patches else None
    best_result.outputs.source_path = patch_path

    return {
        "stem": diagram.stem,
        "origin": diagram.origin,
        "diagram_type": diagram.diagram_type,
        "final_diagram_type": final_diagram_type,
        "best_pass": asdict(best_result),
        "passes": [asdict(item) for item in pass_results],
        "llm_repair": asdict(llm_repair),
    }


def _gallery_html(results: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for index, result in enumerate(results, start=1):
        best_pass = result["best_pass"]
        outputs = best_pass["outputs"]
        title = html.escape(result["origin"])
        light = outputs["light_svg"]
        dark = outputs["dark_svg"]
        patch = outputs["source_path"]
        original_type = result["diagram_type"]
        final_type = result.get("final_diagram_type") or original_type
        type_label = html.escape(final_type if final_type == original_type else f"{original_type} -> {final_type}")
        llm_repair = result.get("llm_repair", {})
        llm_status = "not used"
        if llm_repair.get("attempted"):
            llm_status = "accepted" if llm_repair.get("accepted") else "rejected"
        elif llm_repair.get("enabled"):
            llm_status = llm_repair.get("reason") or "skipped"
        cards.append(
            f"""
<section class="card">
  <header>
    <span class="num">{index}</span>
    <div>
      <h2>{title}</h2>
      <p>type={type_label} | source={html.escape(best_pass['source_variant'])} | pass={best_pass['pass_index']} | strategy={html.escape(best_pass['strategy'])}</p>
    </div>
  </header>
  <div class="grid">
    <div class="panel light">
      <h3>Light</h3>
      {"<img src='" + Path(light).name + "' alt='light'>" if light else "<div class='error'>render failed</div>"}
    </div>
    <div class="panel dark">
      <h3>Dark</h3>
      {"<img src='" + Path(dark).name + "' alt='dark'>" if dark else "<div class='error'>render failed</div>"}
    </div>
  </div>
  <div class="meta">
    <strong>Fixes:</strong> {", ".join(best_pass['applied_fixes']) or "none"}<br>
    <strong>Notes:</strong> {", ".join(best_pass['notes']) or "none"}<br>
    <strong>LLM:</strong> {html.escape(llm_status)}<br>
    <strong>Patch:</strong> {html.escape(Path(patch).name) if patch else "not written"}
  </div>
</section>
"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mermaid Skill Loop Gallery</title>
<style>
body {{
  font-family: Tahoma, Arial, sans-serif;
  background: #111827;
  color: #e5e7eb;
  margin: 0;
  padding: 24px;
}}
h1 {{
  margin: 0 0 8px;
  color: #6fbe44;
}}
.card {{
  background: #0f172a;
  border: 1px solid #1f2937;
  border-radius: 12px;
  margin: 0 0 24px;
  overflow: hidden;
}}
.card header {{
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #1f2937;
}}
.num {{
  background: #6fbe44;
  color: #ffffff;
  border-radius: 999px;
  min-width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}}
.grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
}}
.panel {{
  padding: 16px;
}}
.panel.light {{
  background: #ffffff;
  color: #111827;
}}
.panel.dark {{
  background: #3c3c3c;
}}
.panel img {{
  max-width: 100%;
  display: block;
}}
.meta {{
  padding: 16px 20px;
  border-top: 1px solid #1f2937;
  color: #cbd5e1;
  font-size: 0.9rem;
}}
.error {{
  color: #ef4444;
  font-weight: 700;
}}
@media (max-width: 900px) {{
  .grid {{
    grid-template-columns: 1fr;
  }}
}}
</style>
</head>
<body>
  <h1>Mermaid Skill Closed Loop</h1>
  <p>First-pass deterministic loop using exact-version Mermaid rendering and theme-aware fixes.</p>
  {''.join(cards)}
</body>
</html>
"""


def _copy_best_artifacts(results: list[dict[str, Any]], gallery_dir: Path) -> None:
    for result in results:
        outputs = result["best_pass"]["outputs"]
        for key in ("light_svg", "dark_svg"):
            value = outputs.get(key)
            if not value:
                continue
            source = Path(value)
            target = gallery_dir / source.name
            if source.exists():
                target.write_bytes(source.read_bytes())


def _take_screenshot(index_html: Path, output_path: Path) -> str | None:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        return f"playwright import failed: {exc}"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = browser.new_page(viewport={"width": 1600, "height": 1000})
            page.goto(index_html.as_uri(), wait_until="networkidle", timeout=30000)
            time.sleep(1)
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()
        return None
    except Exception as exc:
        return str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Mermaid skill closed loop")
    parser.add_argument("paths", nargs="+", help="Mermaid files, Markdown files, or directories")
    parser.add_argument(
        "--workspace-root",
        default=str(Path.cwd()),
        help="Workspace root or any path inside the workspace",
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
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory. Defaults to <workspace>/tmp/mermaid-skill-loop",
    )
    parser.add_argument(
        "--include-markdown",
        action="store_true",
        help="Also extract Mermaid blocks from Markdown inputs and directories",
    )
    parser.add_argument(
        "--max-passes",
        type=int,
        default=3,
        help="Maximum passes to evaluate per diagram",
    )
    parser.add_argument(
        "--write-patches",
        action="store_true",
        help="Write suggested Mermaid patch files for the chosen pass",
    )
    parser.add_argument(
        "--enable-llm-repair",
        action="store_true",
        help="Use an OpenAI or Azure OpenAI repair pass when deterministic Mermaid fixes stall",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["auto", "openai", "azure-openai"],
        default="auto",
        help="LLM provider for the optional Mermaid repair pass",
    )
    parser.add_argument(
        "--llm-model",
        default=check_env.DEFAULT_LLM_MODEL,
        help="Model to use for optional Mermaid repair",
    )
    parser.add_argument(
        "--azure-openai-endpoint",
        default=None,
        help="Azure OpenAI chat completions endpoint. Falls back to AZURE_OPENAI_ENDPOINT",
    )
    parser.add_argument(
        "--azure-openai-api-key",
        default=None,
        help="Azure OpenAI API key. Falls back to AZURE_OPENAI_API_KEY",
    )
    parser.add_argument(
        "--azure-openai-deployment",
        default=None,
        help="Azure OpenAI deployment name. Falls back to AZURE_OPENAI_DEPLOYMENT",
    )
    parser.add_argument(
        "--azure-openai-api-version",
        default=None,
        help="Azure OpenAI API version. Falls back to AZURE_OPENAI_API_VERSION",
    )
    parser.add_argument(
        "--llm-threshold",
        type=int,
        default=80,
        help="Minimum deterministic score required to skip the optional LLM repair pass",
    )
    parser.add_argument(
        "--no-screenshot",
        action="store_true",
        help="Skip Playwright gallery screenshot",
    )
    args = parser.parse_args()

    environment = check_env.inspect_environment(
        args.workspace_root,
        env_file=args.env_file,
        project_json=args.project_json,
    )
    if not environment["modes"]["render"]:
        print(check_env._text_summary(environment), file=sys.stderr)
        return 1

    workspace_root = Path(environment["workspace_root"])
    output_dir = Path(args.out_dir) if args.out_dir else workspace_root / "tmp" / "mermaid-skill-loop"
    output_dir.mkdir(parents=True, exist_ok=True)
    llm_settings = _resolve_llm_settings(args, workspace_root)

    diagrams = discover_diagrams([Path(item).expanduser() for item in args.paths], args.include_markdown)
    if not diagrams:
        print("No Mermaid diagrams found.", file=sys.stderr)
        return 1

    results = [
        iterate_diagram(
            diagram=diagram,
            environment=environment,
            llm_settings=llm_settings,
            output_dir=output_dir,
            max_passes=max(1, args.max_passes),
            write_patches=args.write_patches,
            enable_llm_repair=args.enable_llm_repair,
            llm_threshold=max(0, args.llm_threshold),
        )
        for diagram in diagrams
    ]

    report = {
        "workspace_root": environment["workspace_root"],
        "renderer": environment["renderer"],
        "llm": {
            "provider": llm_settings.provider,
            "model": llm_settings.model,
            "available": llm_settings.available,
            "env_file_path": llm_settings.env_file_path,
            "project_json_path": llm_settings.project_json_path,
            "project_json_notice": llm_settings.project_json_notice,
        },
        "diagram_count": len(results),
        "results": results,
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    gallery_dir = output_dir / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    _copy_best_artifacts(results, gallery_dir)
    gallery_path = gallery_dir / "index.html"
    gallery_path.write_text(_gallery_html(results), encoding="utf-8")

    screenshot_path = None
    screenshot_error = None
    if not args.no_screenshot and environment["modes"]["closed_loop"]:
        screenshot_path = gallery_dir / "gallery-screenshot.png"
        screenshot_error = _take_screenshot(gallery_path, screenshot_path)

    summary = {
        "report": str(report_path),
        "gallery": str(gallery_path),
        "screenshot": str(screenshot_path) if screenshot_path and screenshot_path.exists() else None,
        "screenshot_error": screenshot_error,
        "diagrams": len(results),
        "passed": sum(
            1
            for item in results
            if item["best_pass"]["outputs"]["light_ok"] and item["best_pass"]["outputs"]["dark_ok"]
        ),
        "llm_attempted": sum(1 for item in results if item["llm_repair"]["attempted"]),
        "llm_accepted": sum(1 for item in results if item["llm_repair"]["accepted"]),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
