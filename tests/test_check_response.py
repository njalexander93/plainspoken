"""Behavioral oracles from the owner's agreed response policy.

Thresholds and exclusions are acceptance requirements, not measured readability.
Small prose examples below have hand-counted expected values.
"""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_response import check_response


class ResponseCheckTests(unittest.TestCase):
    def test_targets_are_ceilings_and_review_starts_after_300_words(self):
        # Accepted policy: 120 normally, 250 teaching, review over 300.
        for count, mode, exceeded, review in [
            (0, "default", False, False), (120, "default", False, False),
            (121, "default", True, False), (250, "teaching", False, False),
            (251, "teaching", True, False), (300, "teaching", True, False),
            (301, "teaching", True, True),
        ]:
            with self.subTest(count=count, mode=mode):
                result = check_response("word " * count, mode=mode)
                self.assertEqual(result["prose_words"], count)
                self.assertEqual(result["target_exceeded"], exceeded)
                self.assertEqual(result["review_required"], review)

    def test_authored_artifact_has_no_response_style_gate(self):
        result = check_response("word " * 301, scope="artifact")
        self.assertEqual(result, {
            "scope": "artifact", "prose_words": 301, "target_words": None,
            "target_exceeded": False, "review_required": False,
        })

    def test_counts_readable_markdown_labels_and_table_prose(self):
        # Hand count: The build passed (3), Read this guide (3), then wait (2),
        # Name Status (2), Service ready (2). Markup and destinations add none.
        text = ("# The **build** passed.\n\n"
                "1. Read [this guide](https://example.com/long/path).\n"
                "> then wait.\n\n| Name | Status |\n| --- | --- |\n"
                "| Service | ready |\n\n[reference]: https://example.com/ignored\n")
        self.assertEqual(check_response(text)["prose_words"], 12)

    def test_excludes_code_and_logs_but_keeps_surrounding_explanation(self):
        text = ("Build passed.\n\n```python\nprint('many code words')\n````\n"
                "~~~log\nERROR repeated log words\n~~~\n\n"
                "    more ignored code words\n\n"
                "Use `python -m check` now.\n")
        self.assertEqual(check_response(text)["prose_words"], 4)

    def test_shorter_or_different_fence_does_not_end_code(self):
        text = "Before.\n````log\n```\n~~~\nignored words\n````\nAfter."
        self.assertEqual(check_response(text)["prose_words"], 2)

    def test_unclosed_fence_excludes_remainder_and_unmatched_inline_is_prose(self):
        self.assertEqual(check_response("Before.\n```log\nignored words")["prose_words"], 1)
        self.assertEqual(check_response("Keep `unfinished code")["prose_words"], 3)

    def test_malformed_markdown_completes_with_bounded_input(self):
        # An unmatched run must not trigger regex backtracking or hide prose.
        command = [sys.executable, str(Path(__file__).parents[1] / "scripts/check_response.py")]
        for text in ["Keep " + "`" * 1048570, "Keep " + "[" * 1048570]:
            result = subprocess.run(command, input=text, text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["prose_words"], 1)

    def test_inline_code_can_contain_shorter_backtick_runs(self):
        self.assertEqual(check_response("Run ``echo `date` now`` safely.")["prose_words"], 2)

    def test_repeated_incomplete_links_finish_at_input_limit(self):
        command = [sys.executable, str(Path(__file__).parents[1] / "scripts/check_response.py")]
        result = subprocess.run(
            command, input="[x](" * 262144, text=True, capture_output=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["prose_words"], 262144)

    def test_links_keep_labels_and_skip_destinations_and_titles(self):
        # Hand count: Read (1), the guide (2), and (1), status badge (2).
        text = 'Read [the guide](https://example.com "A long title") and ![status badge](image.svg).'
        self.assertEqual(check_response(text)["prose_words"], 6)

    def test_plain_logs_are_not_guessed_away_or_prose_continuations_dropped(self):
        self.assertEqual(check_response("ERROR build failed\n    check the input")["prose_words"], 6)

    def test_word_count_handles_apostrophes_unicode_and_hyphens(self):
        self.assertEqual(check_response("Don't re-run café’s checks.")["prose_words"], 4)

    def test_rejects_invalid_api_input_without_rendering_it(self):
        for kwargs in [{"text": None}, {"text": "secret", "mode": "secret"},
                       {"text": "secret", "scope": "secret"},
                       {"text": "é" * 524289}, {"text": "\ud800"}]:
            with self.subTest(kind=list(kwargs)):
                with self.assertRaises(ValueError) as raised:
                    check_response(**kwargs)
                self.assertNotIn("secret", str(raised.exception))

    def test_cli_rejects_invalid_utf8_and_oversized_input(self):
        command = [sys.executable, str(Path(__file__).parents[1] / "scripts/check_response.py")]
        for data in [b"\xff", b"x" * 1048577]:
            with self.subTest(size=len(data)):
                result = subprocess.run(command, input=data, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"invalid input", result.stderr)

    def test_cli_reviews_long_reply_without_echoing_or_editing_it(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parents[1] / "scripts/check_response.py")],
            input="private " * 301, text=True, capture_output=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout), {
            "scope": "reply", "prose_words": 301, "target_words": 120,
            "target_exceeded": True, "review_required": True,
        })
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
