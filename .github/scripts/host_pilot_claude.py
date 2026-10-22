#!/usr/bin/env python3
"""Launch the installed Claude Code CLI on an exported package and assert its hook callbacks.

The session runs from an empty working directory with an empty Claude config
directory, so only the exported plugin's hooks can run. Without an API key the
CLI still loads the plugin and runs the SessionStart and UserPromptSubmit hooks
before it reports that it is not logged in; those payloads are asserted. With
ANTHROPIC_API_KEY set, a second session asks for a long answer and asserts one
Stop review request followed by a bounded continuation.

A CLI session does not certify the desktop app. The evidence directory keeps the
raw event streams and a pilot.json summary.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REMINDER_MARK = "Answer the requested point"
LONG_PROMPT = (
    "Write at least 450 words of plain prose explaining what a git branch is. "
    "Use no code blocks, no lists and no headings."
)


def parse_output(event: dict[str, object]) -> object:
    """Decode a hook_response output, which hosts deliver as a JSON string."""
    output = event.get("output")
    if isinstance(output, str):
        try:
            return json.loads(output)
        except ValueError:
            return output
    return output


def evaluate(lines: list[str], authenticated: bool) -> dict[str, object]:
    """Judge one stream-json session by its plugin load and hook payloads.

    Args:
        lines: Raw stream-json lines emitted by `claude -p`.
        authenticated: Whether the session had credentials, enabling the Stop checks.

    Returns:
        Named boolean checks, the loaded plugin version, and the session result.
    """
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    plugins = next(
        (e.get("plugins") or [] for e in events if e.get("subtype") == "init"),
        [],
    )
    plugin = next((p for p in plugins if p.get("name") == "plainspoken"), None)
    responses: dict[str, list[object]] = {}
    for event in events:
        if event.get("subtype") == "hook_response":
            responses.setdefault(str(event.get("hook_event")), []).append(parse_output(event))
    result = next((e for e in events if e.get("type") == "result"), {})

    def reminder(event: str) -> bool:
        return any(
            isinstance(o, dict)
            and REMINDER_MARK in str(o.get("hookSpecificOutput", {}).get("additionalContext"))
            for o in responses.get(event, [])
        )

    checks = {
        "plugin_loaded": plugin is not None,
        "session_start_reminder": reminder("SessionStart"),
        "prompt_submit_reminder": reminder("UserPromptSubmit"),
        "session_result_received": bool(result),
    }
    if authenticated:
        stops = responses.get("Stop", [])
        blocks = [o for o in stops if isinstance(o, dict) and o.get("decision") == "block"]
        checks["stop_review_requested"] = len(blocks) == 1
        # The continuation's Stop must return {} so the review ends after one pass.
        checks["stop_review_bounded"] = (
            bool(stops) and stops[-1] == {} and not result.get("is_error")
        )
    return {
        "checks": checks,
        "plugin_version": plugin.get("version") if plugin else None,
        "result": {
            k: result.get(k) for k in ("subtype", "is_error", "num_turns", "total_cost_usd")
        },
    }


def run_session(claude: str, plugin: Path, prompt: str, env: dict[str, str]) -> list[str]:
    """Run one print-mode session from an empty directory and return its stream lines."""
    with tempfile.TemporaryDirectory(prefix="plainspoken cwd ") as cwd:
        completed = subprocess.run(
            [
                claude,
                "--plugin-dir",
                str(plugin),
                "-p",
                prompt,
                "--output-format",
                "stream-json",
                "--verbose",
                "--include-hook-events",
            ],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
        )
    # Exit status is not evidence: the adapter fails open and an unauthenticated run exits 1.
    return completed.stdout.splitlines()


def main() -> int:
    """Run the unauthenticated and, when possible, authenticated sessions and write evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin", required=True, type=Path, help="exported plugin directory")
    parser.add_argument("--out", required=True, type=Path, help="evidence directory")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    claude = shutil.which("claude")
    if claude is None:
        print("claude is not on PATH", file=sys.stderr)
        return 1
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    # Keep host credentials and settings out of the session; only the exported plugin runs.
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDECODE"))
    }
    env["CLAUDE_CONFIG_DIR"] = tempfile.mkdtemp(prefix="plainspoken-config-")

    sessions: dict[str, dict[str, object]] = {}
    lines = run_session(claude, args.plugin, "Use Plainspoken. What is a git branch?", env)
    (args.out / "stream-unauthenticated.jsonl").write_text("\n".join(lines) + "\n")
    sessions["unauthenticated"] = evaluate(lines, authenticated=False)
    if api_key:
        lines = run_session(claude, args.plugin, LONG_PROMPT, {**env, "ANTHROPIC_API_KEY": api_key})
        (args.out / "stream-authenticated.jsonl").write_text("\n".join(lines) + "\n")
        sessions["authenticated"] = evaluate(lines, authenticated=True)
    else:
        sessions["authenticated"] = {
            "skipped": "ANTHROPIC_API_KEY is not configured; Stop review not exercised"
        }

    ok = all(all(s.get("checks", {}).values()) for s in sessions.values())
    summary = {
        "host": "Claude Code CLI",
        "host_version": subprocess.run(
            [claude, "--version"], capture_output=True, text=True, check=False
        ).stdout.strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "plugin_dir": str(args.plugin),
        "sessions": sessions,
        "ok": ok,
    }
    (args.out / "pilot.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
