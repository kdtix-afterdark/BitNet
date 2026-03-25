"""Tests for broker trace monitoring helpers."""

from __future__ import annotations

import unittest

from broker.trace_monitor import format_trace_event, summarize_state


class TraceMonitorTests(unittest.TestCase):
    def test_summarize_state_counts_scripted_inserted_and_skipped_turns(self) -> None:
        state = {
            "session_id": "session-1",
            "next_turn_index": 4,
            "completed": False,
            "broker_turn_count": 3,
            "external_turns_detected": 1,
            "results": [
                {"kind": "inserted", "prompt": "Hi", "response": "Hello"},
                {"kind": "scripted", "prompt": "Story", "response": "Once upon a time"},
                {"kind": "skipped", "prompt": "Skip me", "response": ""},
            ],
        }

        summary = summarize_state(state)

        self.assertEqual(summary["session_id"], "session-1")
        self.assertEqual(summary["scripted_turns"], 1)
        self.assertEqual(summary["inserted_turns"], 1)
        self.assertEqual(summary["skipped_turns"], 1)
        self.assertEqual(summary["latest_kind"], "skipped")

    def test_format_trace_event_renders_raw_model_excerpt(self) -> None:
        event = {
            "correlation_id": "abcdef123456",
            "phase": "llama_response_received",
            "payload": {
                "raw_content": "Hello Chris, you can call me BitNet. How can I assist you today?"
            },
        }

        rendered = format_trace_event(event)

        self.assertIn("corr=abcdef12", rendered)
        self.assertIn("phase=llama_response_received", rendered)
        self.assertIn("Hello Chris", rendered)


if __name__ == "__main__":
    unittest.main()
