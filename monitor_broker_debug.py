"""Live monitor for broker turn traces and conversation UAT sidecar state."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from broker.trace_monitor import format_trace_event, summarize_state


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tail broker turn traces and conversation UAT state together.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        required=True,
        help="Path to a conversation *.state.json sidecar file.",
    )
    parser.add_argument(
        "--trace-jsonl",
        type=Path,
        default=Path("broker_traces/turn-trace.jsonl"),
        help="Path to the append-only broker trace JSONL log.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Polling interval in seconds.",
    )
    args = parser.parse_args()

    state_path = args.state_file.resolve()
    trace_path = args.trace_jsonl.resolve()
    trace_offset = 0
    last_state_mtime_ns = None
    current_session_id = None

    print("Monitoring broker debug streams")
    print(f"  state: {state_path}")
    print(f"  trace: {trace_path}")
    print("Press Ctrl+C to stop.\n")

    while True:
        if state_path.exists():
            stat = state_path.stat()
            if last_state_mtime_ns != stat.st_mtime_ns:
                state = load_json(state_path)
                last_state_mtime_ns = stat.st_mtime_ns
                summary = summarize_state(state)
                current_session_id = summary.get("session_id")
                print(
                    "[state] session=%s next_turn=%s scripted=%s inserted=%s skipped=%s broker_turns=%s external=%s"
                    % (
                        summary.get("session_id"),
                        summary.get("next_turn_index"),
                        summary.get("scripted_turns"),
                        summary.get("inserted_turns"),
                        summary.get("skipped_turns"),
                        summary.get("broker_turn_count"),
                        summary.get("external_turns_detected"),
                    )
                )
                if summary.get("latest_kind"):
                    print(
                        "[state] latest kind=%s prompt=%s response=%s"
                        % (
                            summary.get("latest_kind"),
                            summary.get("latest_prompt_excerpt"),
                            summary.get("latest_response_excerpt"),
                        )
                    )

        if trace_path.exists():
            with trace_path.open("r", encoding="utf-8") as handle:
                handle.seek(trace_offset)
                while True:
                    line = handle.readline()
                    if not line:
                        break
                    trace_offset = handle.tell()
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    session_id = event.get("session_id")
                    if current_session_id and session_id and session_id != current_session_id:
                        continue
                    print(format_trace_event(event))

        time.sleep(max(args.interval, 0.1))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped broker debug monitor.")
