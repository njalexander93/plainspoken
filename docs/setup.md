# Set up Plainspoken

**Install into the coding host you use.** Plainspoken does not install into ordinary ChatGPT or Claude chats.

## Requirements

- Git, to obtain this repository.
- Python 3, available as `python3` to the host's hook commands.
- A host with the plugin features described below.

The commands below use a macOS or Linux shell. Run them from a terminal where your host's command is available.

1. Clone the repository:

   ```sh
   git clone https://github.com/njalexander93/plainspoken.git
   cd plainspoken
   ```

2. Confirm Python is available:

   ```sh
   python3 --version
   ```

3. Follow your host's installation steps below. Replace `/absolute/path/plainspoken` with the full path to this checkout.

## Codex

This integration targets **Codex with local plugin hooks**, including the desktop app. Current Codex documentation distinguishes manually installed plugin hooks from public catalog distribution. See the official [plugin guide](https://developers.openai.com/plugins/build/plugins) and [hook guide](https://learn.chatgpt.com/docs/hooks).

1. Register the local marketplace:

   ```sh
   codex plugin marketplace add "/absolute/path/plainspoken"
   ```

2. Install Plainspoken:

   ```sh
   codex plugin add plainspoken@plainspoken-local
   ```

3. Confirm the plugin appears:

   ```sh
   codex plugin list
   ```

4. Start a new Codex conversation. Ask the assistant to use Plainspoken and answer a short question.

Codex receives reminders when a session starts and when you submit a prompt. Its stop hook can request one follow-up review of an answer over 300 prose words. The hook skips a repeated stop-hook continuation.

To remove the plugin and its local marketplace:

```sh
codex plugin remove plainspoken@plainspoken-local
codex plugin marketplace remove plainspoken-local
```

## Claude Code

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

To remove the persistent installation:

```sh
claude plugin uninstall plainspoken@plainspoken-local --scope user
claude plugin marketplace remove plainspoken-local
```

For the single-session method, exit the session and omit `--plugin-dir` next time.

## Cursor

Cursor uses a local plugin copy, an always-applied rule, and a session reminder. **Cursor has no automatic response check in this first pass.** Its stop event does not supply the answer text needed by this checker. See the official [plugin installation guide](https://cursor.com/docs/plugins), [plugin reference](https://cursor.com/docs/reference/plugins), and [hook reference](https://cursor.com/docs/hooks).

1. Confirm that `~/.cursor/plugins/local/plainspoken` does not already contain an installation you need to preserve.
2. Copy this checkout:

   ```sh
   mkdir -p ~/.cursor/plugins/local
   mkdir ~/.cursor/plugins/local/plainspoken
   plainspoken_source="/absolute/path/plainspoken"
   cp -R "$plainspoken_source/.cursor-plugin" \
     "$plainspoken_source/skills" "$plainspoken_source/rules" \
     "$plainspoken_source/hooks" "$plainspoken_source/scripts" \
     ~/.cursor/plugins/local/plainspoken/
   ```

3. Run **Developer: Reload Window** from Cursor's command palette.
4. Open **Customize** and confirm Plainspoken appears in the plugin inventory.
5. Start a new conversation and ask the assistant to use Plainspoken for a short answer.

To uninstall, remove only `~/.cursor/plugins/local/plainspoken`, then run **Developer: Reload Window** again.

## Check a response manually

Run the shared checker from the repository root:

```sh
python3 scripts/check_response.py < response.md
```

For a teaching reply:

```sh
python3 scripts/check_response.py --mode teaching < response.md
```

For an authored deliverable with its own length requirements:

```sh
python3 scripts/check_response.py --scope artifact < response.md
```

The checker prints JSON with the prose count and review signals. Exit code `0` includes answers that need review. Exit code `2` means invalid arguments, invalid UTF-8, or input over 1 MiB. The checker does not rewrite or upload the input.

## Verify activation

Plugin inventory confirms installation. A short answer confirms only visible behavior. Neither proves every hook ran.

To inspect Claude Code hook events with a temporary installation:

```sh
claude --plugin-dir "/absolute/path/plainspoken" -p 'Use Plainspoken. What is a git branch?' --output-format stream-json --verbose --include-hook-events
```

Use your host's hook diagnostics to confirm session and prompt reminders. A stop hook can flag output over 300 prose words. The assistant must judge whether the output is a conversation reply or a requested artifact. The checker cannot infer that distinction.

## First-pass verification

| Integration | Included behavior | Native verification |
| --- | --- | --- |
| Codex | Skill, session and prompt reminders, bounded stop review | Pending. Do not treat fixture tests as host activation. |
| Claude Code | Skill, session and prompt reminders, bounded stop review | Pending. Manifest and callback runs are separate checks. |
| Cursor | Skill, always-applied rule, session reminder | Pending. Automatic response review is not included. |
| Shared checker | Word counts and advisory signals | Manual CLI examples and 13 unit tests pass on Python 3.13. |

## Development

No third-party Python packages are required. From the repository root, run:

```sh
python3 -m unittest discover -s tests -v
```

When changing host integration, validate the plugin manifests with the host and exercise it in a disposable project. Record actual host runs separately from payload fixtures. See [AGENTS.md](../AGENTS.md) for the contributor entry point.
