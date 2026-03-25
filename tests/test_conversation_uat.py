"""Tests for the interactive conversation UAT runner helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from run_conversation_uat import (
    assess_inserted_prompt_risk,
    derive_state_path,
    find_session_in_recovery,
    load_json,
    managed_turn_count,
    record_skipped_turn,
    save_json,
    scripted_turn_count,
    skipped_turn_count,
    sync_state_with_broker,
)


class ConversationUatTests(unittest.TestCase):
    def test_derive_state_path_uses_sidecar_suffix(self) -> None:
        path = Path("conversations/conversation.test01.json")
        self.assertEqual(
            derive_state_path(path),
            Path("conversations/conversation.test01.state.json"),
        )

    def test_save_and_load_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.state.json"
            payload = {"session_id": "abc", "next_turn_index": 2}
            save_json(path, payload)
            self.assertEqual(load_json(path), payload)

    def test_find_session_in_recovery_uses_sessions_list(self) -> None:
        payload = {
            "sessions": [
                {"session_id": "session-1", "turn_count": 3},
                {"session_id": "session-2", "turn_count": 5},
            ]
        }
        self.assertEqual(
            find_session_in_recovery(payload, "session-2"),
            {"session_id": "session-2", "turn_count": 5},
        )

    def test_sync_state_with_broker_detects_out_of_band_turns(self) -> None:
        state = {
            "session_id": "session-1",
            "results": [
                {"turn_index": 0, "kind": "scripted"},
                {"turn_index": 1, "kind": "scripted"},
            ],
        }

        original = __import__("run_conversation_uat").get_json

        def fake_get_json(base_url: str, path: str) -> dict:
            self.assertEqual(base_url, "http://127.0.0.1:8091")
            self.assertEqual(path, "/recovery/last")
            return {
                "sessions": [
                    {
                        "session_id": "session-1",
                        "turn_count": 3,
                        "message_count": 6,
                        "summary_char_count": 120,
                        "summarized_turn_count": 1,
                    }
                ]
            }

        module = __import__("run_conversation_uat")
        module.get_json = fake_get_json
        try:
            warning = sync_state_with_broker("http://127.0.0.1:8091", state)
        finally:
            module.get_json = original

        self.assertIn("out-of-band", warning or "")
        self.assertEqual(state["broker_turn_count"], 3)
        self.assertEqual(state["external_turns_detected"], 1)

    def test_scripted_and_managed_turn_counts_treat_inserted_turns_differently(self) -> None:
        state = {
            "results": [
                {"kind": "scripted", "turn_index": 0},
                {"kind": "inserted", "turn_index": None},
                {"kind": "scripted", "turn_index": 1},
            ]
        }
        self.assertEqual(scripted_turn_count(state), 2)
        self.assertEqual(managed_turn_count(state), 3)

    def test_managed_turn_count_ignores_skipped_turns(self) -> None:
        state = {
            "results": [
                {"kind": "scripted", "turn_index": 0},
                {"kind": "skipped", "turn_index": 1},
                {"kind": "inserted", "turn_index": None},
            ]
        }
        self.assertEqual(scripted_turn_count(state), 1)
        self.assertEqual(skipped_turn_count(state), 1)
        self.assertEqual(managed_turn_count(state), 2)

    def test_record_skipped_turn_marks_turn_without_response(self) -> None:
        state = {"results": []}

        record_skipped_turn(
            state,
            turn_index=3,
            prompt="Yes, my name is Chris, Can I call you BitNet?",
        )

        self.assertEqual(len(state["results"]), 1)
        item = state["results"][0]
        self.assertEqual(item["kind"], "skipped")
        self.assertEqual(item["turn_index"], 3)
        self.assertEqual(item["prompt"], "Yes, my name is Chris, Can I call you BitNet?")
        self.assertEqual(
            item["original_scripted_prompt"],
            "Yes, my name is Chris, Can I call you BitNet?",
        )
        self.assertEqual(
            item["skip_note"],
            "Skipped by UAT tester. Original scripted prompt preserved for review.",
        )
        self.assertEqual(item["response"], "")
        self.assertEqual(item["route_reason"], "skipped_by_uat_tester")
        self.assertFalse(item["model_invoked"])

    def test_assess_inserted_prompt_risk_warns_when_topic_is_stale(self) -> None:
        state = {
            "results": [
                {
                    "kind": "scripted",
                    "prompt": "write a simple 200 word story about the two of us",
                    "response": "Chris and BitNet wrote a story together.",
                },
                {
                    "kind": "inserted",
                    "prompt": "I have 100 apples in my office",
                    "response": "You currently have 100 apples.",
                },
                {
                    "kind": "scripted",
                    "prompt": "I just was delivered 50 more apples",
                    "response": "You now have 150 apples total.",
                },
                {
                    "kind": "scripted",
                    "prompt": "Can you track apple deliveries?",
                    "response": "Yes, I can track them turn by turn.",
                },
            ]
        }
        warning = assess_inserted_prompt_risk(state, "Could you add to our previous story?")
        self.assertIn("older topic", warning or "")

    def test_assess_inserted_prompt_risk_allows_recent_continuation(self) -> None:
        state = {
            "results": [
                {
                    "kind": "scripted",
                    "prompt": "I have 100 apples in my office",
                    "response": "You currently have 100 apples.",
                },
                {
                    "kind": "inserted",
                    "prompt": "I just was delivered 50 more apples",
                    "response": "You now have 150 apples total.",
                },
            ]
        }
        warning = assess_inserted_prompt_risk(state, "Could you remember our apple total?")
        self.assertIsNone(warning)


if __name__ == "__main__":
    unittest.main()
