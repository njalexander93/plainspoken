# Install Plainspoken in Codex

Complete the [common requirements](../setup.md#requirements) first.
The commands use a macOS or Linux shell. Replace `/absolute/path/plainspoken` with the full path to your checkout.

## Install

This integration targets **Codex with local plugin hooks**, including the desktop app. The current official guide uses desktop installation after CLI marketplace registration. See the official [plugin guide](https://developers.openai.com/plugins/build/plugins) and [hook guide](https://learn.chatgpt.com/docs/hooks).

1. Register the local marketplace:

   ```sh
   codex plugin marketplace add "/absolute/path/plainspoken"
   ```

2. Restart the desktop app. Open the **Plugins Directory**, choose the `plainspoken-local` marketplace, and install Plainspoken.
3. Start Codex in your project and complete its normal folder trust review.
4. Open `/hooks`. Review the Plainspoken commands for `SessionStart`, `UserPromptSubmit`, and `Stop`. Trust only the commands you have reviewed.
5. Start a new conversation. Ask the assistant to use Plainspoken and answer a short question.

The [official installation guide](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)
names the desktop client as the ChatGPT desktop app. This repository has not yet
verified that installation flow in the desktop UI.

Codex receives reminders when a session starts and when you submit a prompt. Its stop hook can request one follow-up review of an answer over 300 prose words. The hook skips a repeated stop-hook continuation.

## Remove

Remove Plainspoken through the desktop app's plugin controls. Then remove its local marketplace:

```sh
codex plugin marketplace remove plainspoken-local
```

## Verify activation

Plugin inventory confirms installation. A short answer confirms only visible behavior.
Neither proves every hook ran. Use the host's hook diagnostics to confirm callback delivery.

A stop hook can flag output over 300 prose words. The assistant must judge whether
the output is a conversation reply or a requested artifact. The checker cannot infer that distinction.

## Observed host runs

Observed on **2026-10-21**, using Codex bundled CLI `0.163.0-alpha.10.2`:

- Project hooks delivered both reminders.
- An answer over 300 words triggered one review, then continuation ended.

Codex Desktop project hooks were also observed on **2026-10-21**:

- A user-typed prompt in a fresh chat produced matching `SessionStart`, `UserPromptSubmit`, and `Stop` receipts.
- The two reminder events returned the canonical skill body. The 35-word answer ended without a review request.
- A separate 346-word answer triggered one review request. The continuation ended without another visible answer.
- All matched callbacks exited successfully. The long answer remained visible.

These instrumented project-hook runs verify Desktop callback delivery and bounded
review behavior. They do not prove marketplace plugin installation, which remains
unverified. The long-answer tests do not demonstrate retraction or a silent replacement.

For problems, see [troubleshooting](../troubleshooting.md).
