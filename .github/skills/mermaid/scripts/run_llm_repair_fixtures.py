#!/usr/bin/env python3
"""
Run the Mermaid skill's intentionally broken LLM repair fixtures.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _iterate_script() -> Path:
    return _skill_root() / "scripts" / "iterate_mermaid.py"


def _default_fixtures_dir() -> Path:
    return _skill_root() / "fixtures" / "llm-repair"


def _build_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(_iterate_script()),
        str(Path(args.fixtures_dir).expanduser()),
        "--workspace-root",
        str(Path(args.workspace_root).expanduser()),
        "--out-dir",
        str(Path(args.out_dir).expanduser()),
        "--enable-llm-repair",
        "--llm-provider",
        args.llm_provider,
        "--llm-threshold",
        str(args.llm_threshold),
        "--max-passes",
        str(args.max_passes),
        "--write-patches",
        "--no-screenshot",
    ]
    if args.env_file:
        command.extend(["--env-file", str(Path(args.env_file).expanduser())])
    if args.project_json:
        command.extend(["--project-json", str(Path(args.project_json).expanduser())])
    return command


def _summarize_result(item: dict[str, Any]) -> dict[str, Any]:
    best_pass = item["best_pass"]
    llm_repair = item["llm_repair"]
    outputs = best_pass["outputs"]
    return {
        "origin": item["origin"],
        "type": item["diagram_type"],
        "source_variant": best_pass["source_variant"],
        "score": best_pass["score"],
        "light_ok": outputs["light_ok"],
        "dark_ok": outputs["dark_ok"],
        "llm_attempted": llm_repair["attempted"],
        "llm_accepted": llm_repair["accepted"],
        "llm_reason": llm_repair["reason"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Mermaid LLM repair fixtures")
    parser.add_argument("--workspace-root", default=str(Path.cwd()), help="Workspace root for Mermaid rendering")
    parser.add_argument("--fixtures-dir", default=str(_default_fixtures_dir()), help="Fixture directory")
    parser.add_argument(
        "--out-dir",
        default=str(Path.cwd() / "tmp" / "mermaid-llm-fixture-run"),
        help="Output directory for iterate_mermaid artifacts",
    )
    parser.add_argument("--llm-provider", choices=["auto", "openai", "azure-openai"], default="auto")
    parser.add_argument("--env-file", default=None, help="Optional .env.mermaid.local path")
    parser.add_argument("--project-json", default=None, help="Optional project.json path")
    parser.add_argument("--llm-threshold", type=int, default=80, help="LLM threshold passed through to iterate_mermaid")
    parser.add_argument("--max-passes", type=int, default=3, help="Max deterministic passes before the repair attempt")
    parser.add_argument(
        "--allow-unaccepted",
        action="store_true",
        help="Do not fail the harness when a fixture was not accepted by the LLM repair path",
    )
    args = parser.parse_args()

    command = _build_command(args)
    result = subprocess.run(command, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout.strip(), file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        return result.returncode

    summary = json.loads(result.stdout)
    report_path = Path(summary["report"])
    report = json.loads(report_path.read_text(encoding="utf-8"))

    failures: list[dict[str, Any]] = []
    per_result = [_summarize_result(item) for item in report["results"]]
    for item in report["results"]:
        best_pass = item["best_pass"]
        llm_repair = item["llm_repair"]
        outputs = best_pass["outputs"]
        if not llm_repair["attempted"]:
            failures.append({"origin": item["origin"], "reason": "LLM repair was not attempted"})
        elif not args.allow_unaccepted and not llm_repair["accepted"]:
            failures.append({"origin": item["origin"], "reason": "LLM repair was not accepted"})
        elif not outputs["light_ok"] or not outputs["dark_ok"]:
            failures.append({"origin": item["origin"], "reason": "accepted result did not render in both themes"})

    harness_summary = {
        "fixtures_dir": args.fixtures_dir,
        "out_dir": args.out_dir,
        "report": str(report_path),
        "diagram_count": report["diagram_count"],
        "results": per_result,
        "failures": failures,
    }
    print(json.dumps(harness_summary, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
