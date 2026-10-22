"""Judge Claude Code CLI stream-json sessions without launching the CLI.

The fixtures follow the event shapes observed on 2026-10-22 with Claude Code 2.1.296.
"""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "host_pilot_claude", ROOT / ".github/scripts/host_pilot_claude.py"
)
assert SPEC is not None and SPEC.loader is not None
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)

REMINDER = json.dumps(
    {
        "hookSpecificOutput": {
            "hookEventName": "x",
            "additionalContext": "## Answer the requested point",
        }
    }
)


def stream(*events: dict) -> list[str]:
    """Serialize events as stream-json lines, with one unparseable line mixed in."""
    return ["not json", *(json.dumps(e) for e in events)]


INIT = {
    "type": "system",
    "subtype": "init",
    "plugins": [{"name": "plainspoken", "version": "0.1.0"}],
}
START = {
    "type": "system",
    "subtype": "hook_response",
    "hook_event": "SessionStart",
    "output": REMINDER,
}
SUBMIT = {
    "type": "system",
    "subtype": "hook_response",
    "hook_event": "UserPromptSubmit",
    "output": REMINDER,
}
RESULT = {"type": "result", "subtype": "success", "is_error": False, "num_turns": 2}


def stop(output: object) -> dict:
    """Build a Stop hook response carrying the given decoded output."""
    return {
        "type": "system",
        "subtype": "hook_response",
        "hook_event": "Stop",
        "output": json.dumps(output),
    }


class HostPilotTests(unittest.TestCase):
    """Verify the pass and fail judgments of the pilot's stream evaluation."""

    def test_unauthenticated_session_passes_on_plugin_and_reminders(self) -> None:
        """Accept a not-logged-in session whose plugin loaded and whose reminders ran."""
        failed = dict(RESULT, is_error=True)
        verdict = pilot.evaluate(stream(INIT, START, SUBMIT, failed), authenticated=False)
        self.assertTrue(all(verdict["checks"].values()), verdict)
        self.assertEqual(verdict["plugin_version"], "0.1.0")
        self.assertNotIn("stop_review_requested", verdict["checks"])

    def test_missing_reminder_or_plugin_fails(self) -> None:
        """Fail when the plugin is absent or a reminder payload lacks the canonical text."""
        no_plugin = pilot.evaluate(stream(START, SUBMIT, RESULT), authenticated=False)
        self.assertFalse(no_plugin["checks"]["plugin_loaded"])
        other = dict(SUBMIT, output=json.dumps({"hookSpecificOutput": {"additionalContext": "x"}}))
        verdict = pilot.evaluate(stream(INIT, START, other, RESULT), authenticated=False)
        self.assertFalse(verdict["checks"]["prompt_submit_reminder"])
        self.assertTrue(verdict["checks"]["session_start_reminder"])

    def test_authenticated_session_requires_one_bounded_review(self) -> None:
        """Require exactly one Stop block followed by an empty continuation response."""
        block = stop({"decision": "block", "reason": "review"})
        good = pilot.evaluate(stream(INIT, START, SUBMIT, block, stop({}), RESULT), True)
        self.assertTrue(all(good["checks"].values()), good)
        for name, events in {
            "no review": [stop({})],
            "unbounded": [block, block],
            "never finished": [block],
        }.items():
            with self.subTest(name=name):
                verdict = pilot.evaluate(stream(INIT, START, SUBMIT, *events, RESULT), True)
                self.assertFalse(all(verdict["checks"].values()), verdict)


if __name__ == "__main__":
    unittest.main()
