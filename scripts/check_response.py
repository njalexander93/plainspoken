#!/usr/bin/env python3
"""Count conversational prose and return advisory review signals.

Purpose:
    Supply the shared observation API used by host adapters and the manual CLI.
    This module never rewrites, stores, uploads, or echoes response text.

Interfaces:
    check_response(text, *, mode='default', scope='reply') returns a JSON-safe
    dictionary. Callers choose default or teaching mode and reply or artifact
    scope. This module cannot infer intent or approve a context exception.
    The CLI accepts UTF-8 stdin and emits one JSON object. Exit 0 includes review
    signals; exit 2 covers invalid arguments, invalid UTF-8, oversized input,
    and caught input I/O errors. Input is limited to 1 MiB in both interfaces.

Processing:
    Remove code blocks and matched inline backtick spans, simplify selected
    Markdown syntax, count words, then attach the scope's targets and signals.
    Reply targets are 120 words by default and 250 in teaching mode. Replies
    over 300 words require review. Artifacts have no target or review flag.

Limits:
    Counting is an English-oriented Markdown approximation, not a full parser.
    Backtick/tilde fences exclude an unclosed fence's remainder. Indented code
    starts after a blank line or at the start of input. Raw log-like lines remain
    prose; put logs in fenced or indented blocks. Simple inline links count
    labels rather than destinations; brackets inside destinations or titles are
    unsupported. Headings, lists, quotes, and table cell prose still count.
    Words are Unicode letter/digit runs with internal apostrophes or hyphens;
    languages without spaces are not segmented. Nested Markdown and HTML may
    differ from a host renderer. Counts cannot prove relevance or comprehension.
"""

import argparse
import json
import re
import sys
from typing import TypedDict

MAX_INPUT_BYTES = 1024 * 1024
_WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
# Brackets bound each candidate scan; malformed links cannot rescan later labels.
_LINK = re.compile(r'!?\[([^][\n]*)\]\([^][\s)]*(?:[ \t]+"[^]["\n]*")?\)')


class ResponseObservations(TypedDict):
    """Describe the counted prose and advisory thresholds for a response.

    Attributes:
        scope: Caller-selected reply or artifact scope.
        prose_words: Number of words remaining after Markdown cleanup.
        target_words: Reply target, or None for an authored artifact.
        target_exceeded: Whether the count exceeds the selected reply target.
        review_required: Whether reply prose exceeds 300 words.
    """

    scope: str
    prose_words: int
    target_words: int | None
    target_exceeded: bool
    review_required: bool


def _without_inline_code(text: str) -> str:
    """Replace matched equal-width backtick spans with spaces.

    Args:
        text: Text to scan for inline code delimiters.

    Returns:
        Text with each matched span, including its delimiters, replaced by one
        space. Unmatched runs remain literal. Matching uses the next run of the
        same width; it does not implement all Markdown inline-code rules.
    """
    # Pair equal-width runs without backtracking on malformed Markdown.
    runs = list(re.finditer(r"`+", text))
    following: list[int | None] = [None] * len(runs)
    last_by_width: dict[int, int] = {}
    # Index the next possible closing run in one reverse pass.
    for index in range(len(runs) - 1, -1, -1):
        width = runs[index].end() - runs[index].start()
        following[index] = last_by_width.get(width)
        last_by_width[width] = index
    pieces: list[str] = []
    start = 0
    index = 0
    # Keep surrounding prose and jump past each complete code span.
    while index < len(runs):
        closing = following[index]
        if closing is None:
            # An unmatched opener must not hide the remaining prose.
            index += 1
            continue
        pieces.extend((text[start : runs[index].start()], " "))
        start = runs[closing].end()
        index = closing + 1
    pieces.append(text[start:])
    return "".join(pieces)


def _prose(text: str) -> str:
    """Extract the approximate Markdown prose used by the word counter.

    Args:
        text: Markdown-like response text.

    Returns:
        Text without recognized code blocks, matched inline code, simple link
        destinations, reference-definition lines, or leading list markers.
        Other markup may remain; this is not rendered Markdown or plain text.
    """
    lines = []
    fence = None
    indented = False
    previous_blank = True
    # Track block state before applying inline cleanup to retained lines.
    for line in text.splitlines():
        match = _FENCE.match(line)
        if fence:
            # Only a same-character, sufficiently wide bare fence closes code.
            if (
                match
                and match[1][0] == fence[0]
                and len(match[1]) >= len(fence)
                and not match[2].strip()
            ):
                fence = None
            continue
        if match and not (match[1][0] == "`" and "`" in match[2]):
            # Backticks in a backtick fence's info string prevent opening it.
            fence = match[1]
            continue
        blank = not line.strip()
        code_indent = line.startswith("    ") or line.startswith("\t")
        if code_indent and (indented or previous_blank):
            # Indentation starts code only at a block boundary or within code.
            indented = True
            continue
        if blank:
            # Retain separators so adjacent prose blocks do not merge.
            previous_blank = True
            lines.append("")
            continue
        indented = False
        previous_blank = False
        lines.append(line)
    # Remove inline code before simplifying links and line-leading markup.
    prose = _without_inline_code("\n".join(lines))
    prose = _LINK.sub(r"\1", prose)
    prose = re.sub(r"^ {0,3}\[[^][\n]+\]:.*$", "", prose, flags=re.MULTILINE)
    prose = re.sub(r"^\s*(?:>\s*)*(?:[-+*]|\d+[.)])\s+", "", prose, flags=re.MULTILINE)
    return prose


def check_response(
    text: str, *, mode: str = "default", scope: str = "reply"
) -> ResponseObservations:
    """Return prose observations without rejecting answers above a target.

    Args:
        text: Response text, encodable as UTF-8 within MAX_INPUT_BYTES.
        mode: 'default' for a 120-word reply target or 'teaching' for 250 words.
        scope: 'reply' for conversational targets or 'artifact' for counting only.

    Returns:
        A dictionary containing scope, prose_words, target_words,
        target_exceeded, and review_required. Artifacts have a None target and
        false flags. Reply flags use strict greater-than comparisons; review
        starts above 300 prose words regardless of mode.

    Raises:
        ValueError: Text is not a string, mode or scope is unsupported, text
            cannot encode as UTF-8, or encoded input exceeds MAX_INPUT_BYTES.
    """
    # Validate the public API boundary before processing or counting text.
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if mode not in ("default", "teaching") or scope not in ("reply", "artifact"):
        raise ValueError("invalid mode or scope")
    # Bound bytes rather than characters, matching the CLI input limit.
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ValueError("text must be valid UTF-8") from error
    if size > MAX_INPUT_BYTES:
        raise ValueError("input exceeds 1 MiB")
    # Attach advisory thresholds only after extracting and counting prose.
    words = len(_WORD.findall(_prose(text)))
    target = (250 if mode == "teaching" else 120) if scope == "reply" else None
    return {
        "scope": scope,
        "prose_words": words,
        "target_words": target,
        "target_exceeded": target is not None and words > target,
        "review_required": scope == "reply" and words > 300,
    }


def main() -> int:
    """Read bounded UTF-8 stdin and print the checker's JSON observations.

    Returns:
        0 after emitting observations, including when review is required; 2
        after reporting caught input, decoding, or validation failures to stderr.

    Raises:
        SystemExit: Argument parsing handles --help or rejects CLI arguments.
        OSError: Writing the JSON result or diagnostic to its stream fails.
    """
    # Restrict CLI options to the same mode and scope values as the API.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("default", "teaching"), default="default")
    parser.add_argument("--scope", choices=("reply", "artifact"), default="reply")
    args = parser.parse_args()
    # Read one byte beyond the limit so oversized input is rejected, not cut.
    try:
        data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise ValueError("input exceeds 1 MiB")
        result = check_response(data.decode("utf-8"), mode=args.mode, scope=args.scope)
    except (ValueError, OSError):
        # Report a fixed diagnostic without exposing any response content.
        print("plainspoken: invalid input (UTF-8 text, at most 1 MiB required)", file=sys.stderr)
        return 2
    # Review signals remain successful observations, not CLI failures.
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
