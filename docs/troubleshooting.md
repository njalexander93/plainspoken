# Troubleshooting

## Replies still look unchanged

1. Start a new conversation after installation.
2. Confirm that your host lists Plainspoken as an enabled plugin.
3. Ask the assistant to use the Plainspoken skill for one reply.
4. Check that another instruction does not require a longer answer or a different format.

A short answer alone does not prove that a hook ran. Check the host's plugin and hook diagnostics before reporting successful activation.

## A long answer appears before a review

The stop hook runs after the assistant's answer. A requested review can create a follow-up answer. It cannot remove text already displayed.

The skill asks the assistant to revise before sending. That instruction depends on the assistant following it.

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
