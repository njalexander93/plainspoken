"""Exercise the checker's command-line contract through a real subprocess.

The in-process API tests live in tests/unit/test_check_response.py.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ResponseCheckCliTests(unittest.TestCase):
    """Verify CLI input handling and output without disclosing input text."""

    def test_malformed_markdown_completes_with_bounded_input(self) -> None:
        """Bound processing time for large unmatched Markdown delimiter runs."""
        # An unmatched run must not trigger regex backtracking or hide prose.
        command = [sys.executable, str(ROOT / "scripts/check_response.py")]
        # Exercise both unmatched delimiter families near the byte limit.
        for text in ["Keep " + "`" * 1048570, "Keep " + "[" * 1048570]:
            result = subprocess.run(command, input=text, text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["prose_words"], 1)

    def test_repeated_incomplete_links_finish_at_input_limit(self) -> None:
        """Process repeated incomplete links within the CLI time bound."""
        command = [sys.executable, str(ROOT / "scripts/check_response.py")]
        # Incomplete links at the byte limit must finish without losing labels.
        result = subprocess.run(
            command,
            input="[x](" * 262144,
            text=True,
            capture_output=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["prose_words"], 262144)

    def test_cli_rejects_invalid_utf8_and_oversized_input(self) -> None:
        """Reject malformed CLI input with a diagnostic and no response payload."""
        command = [sys.executable, str(ROOT / "scripts/check_response.py")]
        # Both encoding and size failures must use the CLI error contract.
        for data in [b"\xff", b"x" * 1048577]:
            with self.subTest(size=len(data)):
                result = subprocess.run(command, input=data, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"invalid input", result.stderr)

    def test_cli_reviews_long_reply_without_echoing_or_editing_it(self) -> None:
        """Return review metadata for a long reply without disclosing its text."""
        # Confirm that a long private reply produces metadata, not echoed text.
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_response.py")],
            input="private " * 301,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(
            json.loads(result.stdout),
            {
                "scope": "reply",
                "prose_words": 301,
                "target_words": 120,
                "target_exceeded": True,
                "review_required": True,
            },
        )
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
