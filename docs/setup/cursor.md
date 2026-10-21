# Install Plainspoken in Cursor

Complete the [common requirements](../setup.md#requirements) first.
The commands use a macOS or Linux shell. Replace `/absolute/path/plainspoken` with the full path to your checkout.

## Install

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

## Remove

To uninstall, remove only `~/.cursor/plugins/local/plainspoken`, then run **Developer: Reload Window** again.

## Verify activation

Plugin inventory confirms installation. A short answer confirms only visible behavior.
Neither proves every hook ran. Use the host's hook diagnostics to confirm callback delivery.

## Observed host runs

Observed on **2026-10-21**, using Cursor `3.25.9`:

- Local plugin discovery showed one skill, one rule, and one hook.
- A short reply ran.
- A captured session-start callback returned the canonical reminder.

Callback capture wrapped the command and ran the unchanged adapter. Automatic
response review is not included.

For problems, see [troubleshooting](../troubleshooting.md).
