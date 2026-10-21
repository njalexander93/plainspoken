#!/usr/bin/env python3
"""Advisory prose observations for host adapters; no rewriting or telemetry.

API: check_response(text, *, mode='default', scope='reply') returns a JSON-safe
dict. mode is default|teaching; scope is reply|artifact. Artifact text is counted
but has no response target or review flag. Callers classify scope and teaching;
this module cannot infer intent or approve an essential-context exception.

CLI: UTF-8 stdin -> one JSON object on stdout. Exit 0 includes review signals;
exit 2 means invalid arguments, UTF-8, or input over 1 MiB. Input is never echoed.

Counting is an English-oriented Markdown approximation, not a full parser:
exclude backtick/tilde fences (including an unclosed fence's remainder), indented
code blocks starting after a blank line, and matched inline backtick spans.
Put logs in fenced/indented blocks; raw log-like lines remain prose. Count link
labels rather than simple inline destinations, headings, lists, quotes, and table
cell prose. Brackets inside destinations/titles are outside this approximation.
Words are Unicode letter/digit runs with internal apostrophes or hyphens. This
does not segment languages without spaces. Nested Markdown and HTML can differ
from a host renderer; no count proves relevance, accessibility, or comprehension.
"""

import argparse
import json
import re
import sys


MAX_INPUT_BYTES = 1024 * 1024
_WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
# Brackets bound each candidate scan; malformed links cannot rescan later labels.
_LINK = re.compile(r'!?\[([^][\n]*)\]\([^][\s)]*(?:[ \t]+"[^]["\n]*")?\)')


def _without_inline_code(text):
    # Pair equal-width runs without backtracking on malformed Markdown.
    runs = list(re.finditer(r"`+", text))
    following = [None] * len(runs)
    last_by_width = {}
    for index in range(len(runs) - 1, -1, -1):
        width = runs[index].end() - runs[index].start()
        following[index] = last_by_width.get(width)
        last_by_width[width] = index
    pieces = []
    start = 0
    index = 0
    while index < len(runs):
        closing = following[index]
        if closing is None:
            index += 1
            continue
        pieces.extend((text[start:runs[index].start()], " "))
        start = runs[closing].end()
        index = closing + 1
    pieces.append(text[start:])
    return "".join(pieces)


def _prose(text):
    lines = []
    fence = None
    indented = False
    previous_blank = True
    for line in text.splitlines():
        match = _FENCE.match(line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if match and not (match[1][0] == "`" and "`" in match[2]):
            fence = match[1]
            continue
        blank = not line.strip()
        code_indent = line.startswith("    ") or line.startswith("\t")
        if code_indent and (indented or previous_blank):
            indented = True
            continue
        if blank:
            previous_blank = True
            lines.append("")
            continue
        indented = False
        previous_blank = False
        lines.append(line)
    prose = _without_inline_code("\n".join(lines))
    prose = _LINK.sub(r"\1", prose)
    prose = re.sub(r"^ {0,3}\[[^][\n]+\]:.*$", "", prose, flags=re.MULTILINE)
    prose = re.sub(r"^\s*(?:>\s*)*(?:[-+*]|\d+[.)])\s+", "", prose, flags=re.MULTILINE)
    return prose


def check_response(text: str, *, mode="default", scope="reply") -> dict:
    """Return observations only; exceeding a target never rejects the response."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if mode not in ("default", "teaching") or scope not in ("reply", "artifact"):
        raise ValueError("invalid mode or scope")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ValueError("text must be valid UTF-8") from error
    if size > MAX_INPUT_BYTES:
        raise ValueError("input exceeds 1 MiB")
    words = len(_WORD.findall(_prose(text)))
    target = (250 if mode == "teaching" else 120) if scope == "reply" else None
    return {
        "scope": scope,
        "prose_words": words,
        "target_words": target,
        "target_exceeded": target is not None and words > target,
        "review_required": scope == "reply" and words > 300,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("default", "teaching"), default="default")
    parser.add_argument("--scope", choices=("reply", "artifact"), default="reply")
    args = parser.parse_args()
    try:
        data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise ValueError("input exceeds 1 MiB")
        result = check_response(data.decode("utf-8"), mode=args.mode, scope=args.scope)
    except (ValueError, OSError):
        print("plainspoken: invalid input (UTF-8 text, at most 1 MiB required)", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
