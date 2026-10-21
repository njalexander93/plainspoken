# Install Plainspoken in Claude Code

Complete the [common requirements](../setup.md#requirements) first.
The commands use a macOS or Linux shell. Replace `/absolute/path/plainspoken` with the full path to your checkout.

## Install

This integration targets **Claude Code**. See the official [plugin reference](https://code.claude.com/docs/en/plugins-reference) and [hook reference](https://code.claude.com/docs/en/hooks).

For a single session, load this checkout directly:

```sh
claude --plugin-dir "/absolute/path/plainspoken"
```

For a persistent user installation:

1. Register the local marketplace:

   ```sh
   claude plugin marketplace add "/absolute/path/plainspoken"
   ```

2. Install Plainspoken:

   ```sh
   claude plugin install plainspoken@plainspoken-local --scope user
   ```

3. Start a new session and open `/plugins`. Confirm Plainspoken is enabled.
4. Ask the assistant to use Plainspoken for a short answer.

Claude Code receives reminders at session start and prompt submission. Its stop hook can request one follow-up review of an answer over 300 prose words. The hook skips a repeated stop-hook continuation.

## Remove

To remove the persistent installation:

```sh
claude plugin uninstall plainspoken@plainspoken-local --scope user
claude plugin marketplace remove plainspoken-local
```

For the single-session method, exit the session and omit `--plugin-dir` next time.

## Verify activation

Plugin inventory confirms installation. A short answer confirms only visible behavior.
Neither proves every hook ran. Use the host's hook diagnostics to confirm callback delivery.

To inspect hook events with a temporary installation:

```sh
claude --plugin-dir "/absolute/path/plainspoken" -p 'Use Plainspoken. What is a git branch?' --output-format stream-json --verbose --include-hook-events
```

A stop hook can flag output over 300 prose words. The assistant must judge whether
the output is a conversation reply or a requested artifact. The checker cannot infer that distinction.

## Observed host runs

Observed on **2026-10-21**, using Claude Code engine `2.1.304`:

- Desktop Code project hooks handled short and long replies, including one review and termination.
- CLI `--plugin-dir` discovered the plugin and delivered both reminders.
- Desktop plugin installation remains unverified. CLI response generation lacked authentication.

Project-hook runs do not prove plugin installation. The long-answer test requested
a review after text was visible. It does not demonstrate retraction or a silent replacement.

For problems, see [troubleshooting](../troubleshooting.md).
