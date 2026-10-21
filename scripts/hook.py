#!/usr/bin/env python3
"""Adapt host hook payloads into canonical reminders and one review request.

Purpose:
    Share a bounded stdin/stdout hook command across Codex, Claude Code, and
    Cursor. Read only the supplied payload and canonical skill file; never read
    transcripts, store responses, or edit an answer.

Interfaces:
    respond(host, payload) returns a JSON-safe host response dictionary.
    The CLI accepts exactly one host name: codex, claude, or cursor. It reads at
    most MAX_INPUT_BYTES + 1 bytes, emits one JSON object, and normally exits 0.
    Unsupported arguments, oversized input, and caught parsing, file, or checker
    failures yield an empty object so advisory checks do not prevent work.

Routing:
    Cursor's sessionStart receives additional_context. Codex and Claude Code
    SessionStart and UserPromptSubmit receive hookSpecificOutput reminders.
    Non-Cursor Stop payloads can request one review above 300 prose words, only
    when stop_hook_active is exactly false and last_assistant_message is text.
    Repeated continuations and unhandled events return an empty object.

Limits:
    The shared checker counts a Stop message as reply prose; the assistant must
    judge actual scope and useful revisions. A review cannot retract visible
    text. Cursor receives reminders only, with no automatic response check.
"""

import json
from pathlib import Path
import sys

from check_response import MAX_INPUT_BYTES, check_response


def respond(host, payload):
    """Build the advisory output for one host event.

    Args:
        host: Host selector. 'cursor' uses Cursor routing; all other values use
            Codex/Claude routing. The CLI restricts this to supported names.
        payload: Decoded hook payload. Non-dictionaries are ignored.

    Returns:
        A host-specific reminder, a Stop review request, or an empty dictionary
        for unsupported events, missing fields, and skipped continuations.
        Reminder content is the canonical skill text after its front matter.

    Raises:
        OSError: Resolving or reading the canonical skill file fails.
        UnicodeDecodeError: The canonical skill file cannot decode as UTF-8.
        ValueError: The shared checker rejects Stop message text, including
            invalid UTF-8 or text exceeding its byte limit.
    """
    # Ignore valid JSON values that cannot contain hook fields.
    if not isinstance(payload, dict):
        return {}
    event = payload.get("hook_event_name")
    # Host event names differ in case and supported reminder timing.
    reminder = event == "sessionStart" if host == "cursor" else event in (
        "SessionStart", "UserPromptSubmit"
    )
    if reminder:
        # Load the rule source at event time so reminders stay canonical.
        skill = Path(__file__).resolve().parents[1] / "skills/plainspoken/SKILL.md"
        context = skill.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        if host == "cursor":
            # Cursor expects context directly on the response object.
            return {"additional_context": context}
        # Codex and Claude attach context to a named hook event.
        return {"hookSpecificOutput": {
            "hookEventName": event, "additionalContext": context,
        }}
    if host != "cursor" and event == "Stop":
        # Require an explicit first stop to avoid repeated review requests.
        text = payload.get("last_assistant_message")
        if payload.get("stop_hook_active") is not False or not isinstance(text, str):
            return {}
        if check_response(text)["review_required"]:
            # Ask for one scope-aware review without claiming to retract text.
            return {
                "decision": "block",
                "reason": (
                    "Plainspoken advisory: review this response once. "
                    "Apply the canonical plainspoken skill to conversational prose; "
                    "authored documents, emails, and other deliverables are outside its scope. "
                    "Simplify only when that preserves essential facts, conditions, uncertainty, "
                    "quotations, and exact code. Do not narrate this review or add a review summary. "
                    "If no useful revision exists or the text is outside scope, "
                    "finish without additional prose. "
                    "Visible text cannot be retracted by this review."
                ),
            }
    # Unhandled events and answers below the review boundary need no output.
    return {}


def main():
    """Read one supported host payload and print its JSON hook response.

    Returns:
        0 after emitting a response. Invalid arguments, oversized input, and
        caught OSError, ValueError, or RecursionError failures emit {}.

    Raises:
        OSError: Writing the JSON response to stdout fails.
    """
    output = {}
    # Ignore unsupported invocations without consuming stdin.
    if len(sys.argv) == 2 and sys.argv[1] in ("codex", "claude", "cursor"):
        try:
            # Detect oversized input before decoding or parsing any payload.
            data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
            if len(data) <= MAX_INPUT_BYTES:
                output = respond(sys.argv[1], json.loads(data.decode("utf-8")))
        except (OSError, ValueError, RecursionError):
            # Style checks must not block work when their input or files are unavailable.
            pass
    # Every handled path emits one JSON object for the host to consume.
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
