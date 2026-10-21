#!/usr/bin/env python3
"""Bounded, advisory host hooks. No transcript reads, response storage, or edits."""

import json
from pathlib import Path
import sys

from check_response import MAX_INPUT_BYTES, check_response


def respond(host, payload):
    if not isinstance(payload, dict):
        return {}
    event = payload.get("hook_event_name")
    reminder = event == "sessionStart" if host == "cursor" else event in (
        "SessionStart", "UserPromptSubmit"
    )
    if reminder:
        skill = Path(__file__).resolve().parents[1] / "skills/plainspoken/SKILL.md"
        context = skill.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        if host == "cursor":
            return {"additional_context": context}
        return {"hookSpecificOutput": {
            "hookEventName": event, "additionalContext": context,
        }}
    if host != "cursor" and event == "Stop":
        text = payload.get("last_assistant_message")
        if payload.get("stop_hook_active") is not False or not isinstance(text, str):
            return {}
        if check_response(text)["review_required"]:
            return {
                "decision": "block",
                "reason": (
                    "Plainspoken advisory: review this response once. "
                    "Apply the canonical plainspoken skill to conversational prose; "
                    "authored documents, emails, and other deliverables are outside its scope. "
                    "Simplify only when that preserves essential facts, conditions, uncertainty, "
                    "quotations, and exact code. If no useful simplification exists or the text "
                    "is outside scope, finish without repeating the answer. "
                    "Visible text cannot be retracted by this review."
                ),
            }
    return {}


def main():
    output = {}
    if len(sys.argv) == 2 and sys.argv[1] in ("codex", "claude", "cursor"):
        try:
            data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
            if len(data) <= MAX_INPUT_BYTES:
                output = respond(sys.argv[1], json.loads(data.decode("utf-8")))
        except (OSError, ValueError, RecursionError):
            # Style checks must not block work when their input or files are unavailable.
            pass
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
