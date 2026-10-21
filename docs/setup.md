# Set up Plainspoken

**Choose your coding host.** Ordinary ChatGPT and Claude chats are not covered by these integrations.

| Host | Installation, activation, removal, and observed runs |
| --- | --- |
| Codex | [Install in Codex](setup/codex.md) |
| Claude Code | [Install in Claude Code](setup/claude.md) |
| Cursor | [Install in Cursor](setup/cursor.md) |

## Requirements

- Git, to obtain this repository.
- Python 3.11 or newer, available as `python3` to the host's hook commands.
- The plugin features described in your host's guide above.

No third-party Python packages or Poetry installation are needed to run Plainspoken.
Poetry manages the separate [development environment](development.md).

The installation commands use a macOS or Linux shell. Native Windows host hooks
remain unverified. Python checks on Windows do not establish host activation.

1. Clone the repository:

   ```sh
   git clone https://github.com/njalexander93/plainspoken.git
   cd plainspoken
   ```

2. Confirm Python is available to your host:

   ```sh
   python3 --version
   ```

3. Follow the installation guide for your host above.

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

## Development

Use the [development guide](development.md) for Poetry setup, local checks, and CI coverage.
See [troubleshooting](troubleshooting.md) for installation or hook failures.
