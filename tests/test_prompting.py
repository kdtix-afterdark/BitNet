"""Focused tests for broker prompt construction."""

from __future__ import annotations

import unittest

from broker.prompting import build_messages


class PromptingTests(unittest.TestCase):
    def test_build_messages_includes_recovered_summary_in_system_prompt(self) -> None:
        messages = build_messages(
            system_prompt="You are a helpful local assistant.",
            user_prompt="What do you remember?",
            evidence_items=[],
            conversation_summary="User: Hi BitNet, my name is Chris\nAssistant: Hello Chris!",
            summarized_turn_count=2,
            conversation_history=[
                {"role": "user", "content": "Latest question"},
                {"role": "assistant", "content": "Latest answer"},
            ],
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Recovered conversation summary", messages[0]["content"])
        self.assertIn("my name is Chris", messages[0]["content"])
        self.assertEqual(messages[1]["content"], "Latest question")
        self.assertEqual(messages[2]["content"], "Latest answer")

    def test_build_messages_keeps_plain_chat_prompt_plain_when_no_evidence_exists(self) -> None:
        messages = build_messages(
            system_prompt="You are a helpful local assistant.",
            user_prompt="what is my name?",
            evidence_items=[],
            conversation_history=[
                {"role": "user", "content": "Hi BitNet, my name is Chris"},
                {"role": "assistant", "content": "Hello Chris!"},
            ],
            grounded_user_prompt=False,
        )

        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], "what is my name?")
        self.assertNotIn("Evidence:", messages[-1]["content"])
        self.assertNotIn("Task:", messages[-1]["content"])

    def test_build_messages_deduplicates_repeated_low_information_assistant_greetings(self) -> None:
        greeting = "Hello Chris, I'm BitNet. How can I assist you today?"
        messages = build_messages(
            system_prompt="You are a helpful local assistant.",
            user_prompt="write a simple story",
            evidence_items=[],
            conversation_history=[
                {"role": "user", "content": "I'm conducting some test prompts."},
                {"role": "assistant", "content": greeting},
                {"role": "user", "content": "Yes, my name is Chris, Can I call you BitNet?"},
                {"role": "assistant", "content": greeting},
            ],
            grounded_user_prompt=False,
        )

        assistant_greetings = [
            message
            for message in messages[:-1]
            if message["role"] == "assistant" and message["content"] == greeting
        ]
        user_turns = [
            message["content"]
            for message in messages[:-1]
            if message["role"] == "user"
        ]

        self.assertEqual(len(assistant_greetings), 1)
        self.assertIn("I'm conducting some test prompts.", user_turns)
        self.assertIn("Yes, my name is Chris, Can I call you BitNet?", user_turns)


if __name__ == "__main__":
    unittest.main()
