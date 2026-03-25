"""Focused tests for broker chat postprocessing."""

from __future__ import annotations

import unittest

from broker.postprocess import repair_chat_response


class PostprocessTests(unittest.TestCase):
    def test_repair_chat_response_trims_role_label_spillover(self) -> None:
        prompt = "Thank you for that story, I liked it :)"
        response = (
            "You're welcome, Chris! I'm glad you enjoyed the story.\n\n"
            "If you have any more questions, feel free to ask.\n\n"
            'User: I\'m going to say something like "Yes, my name is Chris, Can I call you BitNet?"\n'
            "Assistant: Hello Chris..."
        )

        repaired, applied, reason = repair_chat_response(prompt, response, evidence_items=[])

        self.assertTrue(applied)
        self.assertEqual(reason, "trimmed_role_label_spillover")
        self.assertNotIn("\nUser:", repaired)
        self.assertEqual(
            repaired,
            "You're welcome, Chris! I'm glad you enjoyed the story.\n\n"
            "If you have any more questions, feel free to ask.",
        )

    def test_repair_chat_response_keeps_requested_transcript_format(self) -> None:
        prompt = "Write a short transcript between User and Assistant"
        response = "User: Hi there\nAssistant: Hello Chris"

        repaired, applied, reason = repair_chat_response(prompt, response, evidence_items=[])

        self.assertFalse(applied)
        self.assertIsNone(reason)
        self.assertEqual(repaired, response)

    def test_repair_chat_response_trims_repeated_assistant_prefix_from_history(self) -> None:
        prompt = "I do not have a method yet to send you files. Working on it."
        previous = (
            "Hello Chris, you can call me BitNet. How can I assist you today?\n\n"
            "It seems like you're experiencing issues with multiple replies popping up."
        )
        response = (
            previous
            + "\n\n"
            + "If you have any specific tools or commands you're trying to use, please let me know."
        )

        repaired, applied, reason = repair_chat_response(
            prompt,
            response,
            evidence_items=[],
            conversation_history=[
                {"role": "assistant", "content": previous},
            ],
        )

        self.assertTrue(applied)
        self.assertIn("trimmed_repeated_assistant_prefix", reason or "")
        self.assertNotIn("How can I assist you today?", repaired)
        self.assertEqual(
            repaired,
            "If you have any specific tools or commands you're trying to use, please let me know.",
        )

    def test_repair_chat_response_collapses_duplicate_paragraph_loops(self) -> None:
        prompt = "Without repeating earlier lines, continue the story in 80 words"
        greeting = "Hello Chris, you can call me BitNet. How can I assist you today?"
        repeated = (
            'One day, Chris said, "BitNet, can I call you BitNet?" BitNet laughed and replied, '
            '"Sure, Chris, you can call me BitNet." They both laughed and continued their project.'
        )
        response = (
            greeting
            + "\n\n"
            + "Once Chris and BitNet were back to their coding project, they decided to keep building.\n\n"
            + repeated
            + "\n\n"
            + repeated
            + "\n\n"
            + repeated
        )

        repaired, applied, reason = repair_chat_response(
            prompt,
            response,
            evidence_items=[],
            conversation_history=[
                {"role": "assistant", "content": greeting},
            ],
        )

        self.assertTrue(applied)
        self.assertIn("trimmed_repeated_assistant_prefix", reason or "")
        self.assertIn("collapsed_duplicate_paragraphs", reason or "")
        self.assertNotIn(greeting, repaired)
        self.assertEqual(repaired.count(repeated), 1)


if __name__ == "__main__":
    unittest.main()
