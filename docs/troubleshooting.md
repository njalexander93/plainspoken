# Troubleshooting

Use your host's guide for installation and activation checks: [Codex](setup/codex.md), [Claude Code](setup/claude.md), or [Cursor](setup/cursor.md).

## Replies still look unchanged

1. Start a new conversation after installation.
2. Confirm that your host lists Plainspoken as an enabled plugin.
3. Follow your host guide's activation checks and inspect hook trust where required.
4. Ask the assistant to use the Plainspoken skill for one reply.
5. Check that another instruction does not require a longer answer or a different format.

A short answer alone does not prove that a hook ran. Check the host's plugin and hook diagnostics before reporting successful activation.

## A long answer appears before a review

The stop hook runs after the assistant's answer. A requested review can create a follow-up answer. It cannot remove text already displayed.

The skill asks the assistant to revise before sending. That instruction depends on the assistant following it. A model may still add a brief review confirmation even when the hook asks it to stop without extra prose.

## A long answer passes the checker

The checker excludes fenced code, indented code, and inline code. Put logs inside code blocks to exclude them. Raw log lines count as prose.

Requested artifacts use their own length requirements. The skill allows longer replies when shortening would lose essential context. Its output is advice, not a quality score.

## The word count looks wrong

The checker uses an English-oriented approximation of Markdown. It counts link labels, headings, quotations, and table prose. It does not reliably segment languages that omit spaces.

Check the input with the [manual checker](setup.md#check-a-response-manually). Preserve meaning when you revise. Do not delete conditions or uncertainty to hit a number.

## A hook fails

1. Confirm that `python3 --version` works in the environment that starts your host.
2. Keep the installed plugin directory intact. Hook commands use files inside it.
3. Inspect the host's hook diagnostics for the command and error.
4. Reinstall from the current checkout if an update left mixed files.

Report the host name, version, installation method, and error. Use a short synthetic response to reproduce the problem. Remove private conversation text from reports.

## The plugin icon is missing

1. Confirm that the installed plugin includes `assets/icon.svg`.
2. Check the field for your host in the [branding reference](setup.md#plugin-branding).
3. Update or reinstall the plugin if its installed copy predates the branding assets.

Claude's `icon` field is for Anthropic's directory listing. It does not add an icon
inside Claude Code. See the official [directory listing reference](https://code.claude.com/docs/en/plugins-reference#directory-listing-fields).

The manifests reference the shared SVG. Display in host interfaces remains unverified.

## Development checks fail

Use the [development guide](development.md) to select the pinned interpreter,
sync the locked Poetry environment, and run the checks. A development environment
pass does not prove that a host can find `python3` or load Plainspoken's hooks.

If `scripts/hook.py` reports 0% coverage on macOS, run `python -v -c pass` in the
environment and look for "Skipping hidden .pth file". Python 3.13 ignores `.pth` files
with the hidden flag, which disables subprocess coverage. `chflags -R nohidden .venv`
restores it. Observed on 2026-10-22 in a worktree whose files all carried the flag.
