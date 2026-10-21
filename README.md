<p align="center">
  <img src="assets/banner.svg" alt="Plainspoken. Plain answers. Less repetition. A deadpan speech bubble on a pale violet background." width="1200">
</p>

# Plainspoken

**Clear replies for coding assistants. Enough said.**

Plainspoken gives coding assistants shared response preferences: answer the question first, use simple language, and stop when the useful answer is complete.

[Install](#pick-your-host) · [Response rules](skills/plainspoken/SKILL.md) · [Troubleshooting](docs/troubleshooting.md) · [Contribute](docs/development.md)

## Pick your host

| Codex | Claude Code | Cursor |
| --- | --- | --- |
| [Install in Codex](docs/setup/codex.md) | [Install in Claude Code](docs/setup/claude.md) | [Install in Cursor](docs/setup/cursor.md) |

Start with the [shared requirements](docs/setup.md). Ordinary ChatGPT and Claude chats are separate products and are not covered by these integrations.

## What changes

- **Answer first.** Lead with the useful point.
- **Keep it readable.** Use short paragraphs, bullets for distinct points, and numbers for steps.
- **Explain the jargon.** Define unfamiliar technical terms when they first appear.
- **Know when to stop.** Aim for 120 words in ordinary replies and 250 when teaching.
- **Keep you informed.** Give concise progress updates during work.

Review replies over **300 words**. Keep essential facts, conditions, and uncertainty.

These preferences apply to **conversation replies**. Documents, emails, and other requested deliverables keep their own requirements. Code and logs do not count toward prose targets.

The [response skill](skills/plainspoken/SKILL.md) owns the full rules. The shared checker flags mechanical review signals; it cannot judge whether an answer is clear or complete.

## How review works

The skill instructs the assistant to review its writing before sending it. Hooks can request a review after an answer. They cannot retract text already shown to you.

## Make it better

Use [AGENTS.md](AGENTS.md) for the contributor entry point. Follow [development setup and checks](docs/development.md) before proposing changes.

The [SVG icon](assets/icon.svg) and [README banner](assets/banner.svg) live in `assets/`.

## License

[MIT](LICENSE). Copyright 2026 Nikolai Alexander.
