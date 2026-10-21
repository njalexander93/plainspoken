"""Verify host hook payload contracts and packaged command invocation.

OpenAI/Claude and Cursor contracts were verified on 2026-10-21.

These are documented payload fixtures, not recordings or native acceptance.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AdapterTests(unittest.TestCase):
    """Verify documented hook payloads and packaged command behavior."""

    def run_hook(self, host, payload):
        """Run one host hook with a JSON payload and decode its response.

        Args:
            host: Host adapter name passed to the hook command.
            payload: JSON-serializable event payload supplied on standard input.

        Returns:
            The decoded JSON response from the hook.

        Raises:
            subprocess.CalledProcessError: If the hook command fails.
            AssertionError: If the hook writes to standard error.
            json.JSONDecodeError: If the hook response is not valid JSON.
        """
        # Exercise the command boundary with the supplied payload.
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/hook.py"), host],
            input=json.dumps(payload).encode(), capture_output=True, check=True,
        )
        self.assertEqual(result.stderr, b"")
        return json.loads(result.stdout)

    def test_submit_delivers_canonical_rules_as_model_context(self):
        """Check that prompt submission supplies the canonical response rules."""
        # Inspect the model context produced by a prompt-submission event.
        output = self.run_hook("codex", {"hook_event_name": "UserPromptSubmit"})
        context = output["hookSpecificOutput"]
        self.assertEqual(context["hookEventName"], "UserPromptSubmit")
        self.assertIn("120 prose words", context["additionalContext"])
        self.assertIn("Preserve the meaning", context["additionalContext"])

    def test_stop_requests_one_review_above_300_words(self):
        """Check the stop-review boundary for both blocking hook hosts."""
        # Both blocking adapters must agree at and above the review boundary.
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.assertEqual(self.run_hook(host, {
                    "hook_event_name": "Stop", "stop_hook_active": False,
                    "last_assistant_message": "word " * 300,
                }), {})
                review = self.run_hook(host, {
                    "hook_event_name": "Stop", "stop_hook_active": False,
                    "last_assistant_message": "word " * 301,
                })
                self.assertEqual(review["decision"], "block")
                self.assertIn("outside its scope", review["reason"])
                self.assertIn("preserves essential facts", review["reason"])

    def test_stop_allows_continuation_to_finish_even_when_still_long(self):
        """Allow stops unless the host explicitly marks the first review attempt."""
        # Only literal False permits a first review; other values must finish.
        for active in (True, None, "false", 0):
            with self.subTest(active=active):
                self.assertEqual(self.run_hook("claude", {
                    "hook_event_name": "Stop", "stop_hook_active": active,
                    "last_assistant_message": "word " * 400,
                }), {})

    def test_code_only_reply_does_not_request_review(self):
        """Exclude fenced code from the stop-review word threshold."""
        self.assertEqual(self.run_hook("codex", {
            "hook_event_name": "Stop", "stop_hook_active": False,
            "last_assistant_message": "```text\n" + "log " * 500 + "\n```",
        }), {})

    def test_cursor_reminder_does_not_invent_stop_or_prompt_injection(self):
        """Limit Cursor output to its supported session-start reminder."""
        # Confirm the supported reminder before checking unsupported events.
        context = self.run_hook("cursor", {"hook_event_name": "sessionStart"})
        self.assertIn("250", context["additional_context"])
        self.assertEqual(self.run_hook("cursor", {
            "hook_event_name": "stop", "status": "completed", "loop_count": 0,
            "text": "word " * 400,
        }), {})
        self.assertEqual(self.run_hook("cursor", {
            "hook_event_name": "beforeSubmitPrompt", "prompt": "Hello",
        }), {})

    def test_missing_or_invalid_message_allows_stop(self):
        """Allow completion when the assistant message is absent or malformed."""
        # Malformed message shapes must not prevent host completion.
        for text in (None, [], {"text": "word " * 400}):
            with self.subTest(text=type(text).__name__):
                self.assertEqual(self.run_hook("claude", {
                    "hook_event_name": "Stop", "stop_hook_active": False,
                    "last_assistant_message": text,
                }), {})

    def test_invalid_input_fails_open_without_echoing_private_text(self):
        """Return an empty hook response for invalid or oversized input."""
        # Cover malformed JSON, invalid encoding, wrong shape, and the size cap.
        for data in (b"private malformed {", b"\xff", b"[]", b"x" * (1024 * 1024 + 1)):
            with self.subTest(size=len(data)):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/hook.py"), "codex"],
                    input=data, capture_output=True, check=True,
                )
                self.assertEqual(json.loads(result.stdout), {})
                self.assertEqual(result.stderr, b"")

    def test_packaged_commands_work_outside_plugin_with_spaces_in_path(self):
        """Exercise manifest commands from a copied plugin path containing spaces."""
        # Reproduce installation paths and working directories with spaces.
        with tempfile.TemporaryDirectory(prefix="plainspoken plugin ") as directory:
            plugin = Path(directory) / "plugin copy"
            # Copy the runtime dependencies needed by packaged commands.
            for folder in ("scripts", "skills"):
                shutil.copytree(ROOT / folder, plugin / folder)
            environment = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin), CURSOR_PLUGIN_ROOT=str(plugin))
            # Execute each manifest command using its host-specific event shape.
            for host in ("codex", "claude", "cursor"):
                with self.subTest(host=host):
                    manifest = json.loads((ROOT / ("." + host + "-plugin") / "plugin.json").read_text())
                    hooks = json.loads((ROOT / manifest["hooks"]).read_text())["hooks"]
                    # Cursor nests its hook definition differently from the other hosts.
                    event = "sessionStart" if host == "cursor" else "SessionStart"
                    definition = hooks[event][0]
                    handler = definition if host == "cursor" else definition["hooks"][0]
                    result = subprocess.run(
                        handler["command"], shell=True, cwd=directory, env=environment,
                        input=json.dumps({"hook_event_name": event}).encode(),
                        capture_output=True, check=True,
                    )
                    output = json.loads(result.stdout)
                    context = output.get("additional_context") or output["hookSpecificOutput"]["additionalContext"]
                    self.assertIn("Answer the requested point", context)


if __name__ == "__main__":
    unittest.main()
