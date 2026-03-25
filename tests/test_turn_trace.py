"""Tests for broker turn trace capture."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from broker.turn_trace import TurnTraceRecorder


class TurnTraceRecorderTests(unittest.TestCase):
    def test_record_writes_jsonl_and_per_turn_trace_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            trace_dir = Path(temp_dir) / "broker_traces"
            recorder = TurnTraceRecorder(trace_dir=trace_dir, enabled=True)

            recorder.record(
                correlation_id="corr-1",
                session_id="session-1",
                phase="turn_started",
                payload={"prompt": "Hi BitNet"},
            )
            recorder.record(
                correlation_id="corr-1",
                session_id="session-1",
                phase="raw_model_response",
                payload={"content": "Hello Chris"},
            )

            jsonl_path = trace_dir / "turn-trace.jsonl"
            turn_path = trace_dir / "turns" / "corr-1.json"

            self.assertTrue(jsonl_path.exists())
            self.assertTrue(turn_path.exists())

            events = [
                json.loads(line)
                for line in jsonl_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["phase"], "turn_started")
            self.assertEqual(events[1]["phase"], "raw_model_response")

            turn_trace = json.loads(turn_path.read_text(encoding="utf-8"))
            self.assertEqual(turn_trace["correlation_id"], "corr-1")
            self.assertEqual(turn_trace["session_id"], "session-1")
            self.assertEqual(len(turn_trace["phases"]), 2)
            self.assertEqual(turn_trace["phases"][0]["payload"]["prompt"], "Hi BitNet")
            self.assertEqual(turn_trace["phases"][1]["payload"]["content"], "Hello Chris")

    def test_record_is_noop_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            trace_dir = Path(temp_dir) / "broker_traces"
            recorder = TurnTraceRecorder(trace_dir=trace_dir, enabled=False)

            recorder.record(
                correlation_id="corr-2",
                session_id="session-2",
                phase="turn_started",
                payload={"prompt": "Hello"},
            )

            self.assertFalse(trace_dir.exists())


if __name__ == "__main__":
    unittest.main()
