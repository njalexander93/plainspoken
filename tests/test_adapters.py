"""Host contracts: OpenAI/Claude hooks and Cursor hooks, verified 2026-10-21.

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
    def run_hook(self, host, payload):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/hook.py"), host],
            input=json.dumps(payload).encode(), capture_output=True, check=True,
        )
        self.assertEqual(result.stderr, b"")
        return json.loads(result.stdout)

    def test_submit_delivers_canonical_rules_as_model_context(self):
        output = self.run_hook("codex", {"hook_event_name": "UserPromptSubmit"})
        context = output["hookSpecificOutput"]
        self.assertEqual(context["hookEventName"], "UserPromptSubmit")
        self.assertIn("120 prose words", context["additionalContext"])
        self.assertIn("Preserve the meaning", context["additionalContext"])

    def test_stop_requests_one_review_above_300_words(self):
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
        for active in (True, None, "false", 0):
            with self.subTest(active=active):
                self.assertEqual(self.run_hook("claude", {
                    "hook_event_name": "Stop", "stop_hook_active": active,
                    "last_assistant_message": "word " * 400,
                }), {})

    def test_code_only_reply_does_not_request_review(self):
        self.assertEqual(self.run_hook("codex", {
            "hook_event_name": "Stop", "stop_hook_active": False,
            "last_assistant_message": "```text\n" + "log " * 500 + "\n```",
        }), {})

    def test_cursor_reminder_does_not_invent_stop_or_prompt_injection(self):
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
        for text in (None, [], {"text": "word " * 400}):
            with self.subTest(text=type(text).__name__):
                self.assertEqual(self.run_hook("claude", {
                    "hook_event_name": "Stop", "stop_hook_active": False,
                    "last_assistant_message": text,
                }), {})

    def test_invalid_input_fails_open_without_echoing_private_text(self):
        for data in (b"private malformed {", b"\xff", b"[]", b"x" * (1024 * 1024 + 1)):
            with self.subTest(size=len(data)):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/hook.py"), "codex"],
                    input=data, capture_output=True, check=True,
                )
                self.assertEqual(json.loads(result.stdout), {})
                self.assertEqual(result.stderr, b"")

    def test_packaged_commands_work_outside_plugin_with_spaces_in_path(self):
        with tempfile.TemporaryDirectory(prefix="plainspoken plugin ") as directory:
            plugin = Path(directory) / "plugin copy"
            for folder in ("scripts", "skills"):
                shutil.copytree(ROOT / folder, plugin / folder)
            environment = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin), CURSOR_PLUGIN_ROOT=str(plugin))
            for host in ("codex", "claude", "cursor"):
                with self.subTest(host=host):
                    manifest = json.loads((ROOT / ("." + host + "-plugin") / "plugin.json").read_text())
                    hooks = json.loads((ROOT / manifest["hooks"]).read_text())["hooks"]
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
