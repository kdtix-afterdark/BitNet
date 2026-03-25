"""Per-turn broker trace capture for root-cause debugging."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TurnTraceRecorder:
    """Persist append-only and per-turn trace artifacts keyed by correlation id."""

    def __init__(self, trace_dir: Path, enabled: bool) -> None:
        self.trace_dir = trace_dir
        self.enabled = bool(enabled)
        self._lock = threading.Lock()

    def record(
        self,
        *,
        correlation_id: str,
        session_id: Optional[str],
        phase: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.enabled or not correlation_id.strip():
            return

        recorded_at = _utc_now()
        event = {
            "recorded_at": recorded_at,
            "correlation_id": correlation_id,
            "session_id": session_id,
            "phase": phase,
            "payload": payload or {},
        }

        with self._lock:
            turns_dir = self.trace_dir / "turns"
            turns_dir.mkdir(parents=True, exist_ok=True)

            jsonl_path = self.trace_dir / "turn-trace.jsonl"
            with jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")

            turn_path = turns_dir / f"{correlation_id}.json"
            if turn_path.exists():
                turn_trace = json.loads(turn_path.read_text(encoding="utf-8"))
            else:
                turn_trace = {
                    "correlation_id": correlation_id,
                    "session_id": session_id,
                    "created_at": recorded_at,
                    "updated_at": recorded_at,
                    "phases": [],
                }

            turn_trace["session_id"] = session_id
            turn_trace["updated_at"] = recorded_at
            turn_trace.setdefault("phases", []).append(
                {
                    "recorded_at": recorded_at,
                    "phase": phase,
                    "payload": payload or {},
                }
            )
            turn_path.write_text(
                json.dumps(turn_trace, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
