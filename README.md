# Plainspoken

**Plain answers. Less repetition.**

Plainspoken gives coding assistants shared response preferences: answer the question first, use simple language, and stop when the useful answer is complete.

## Behavior

- Aim for **120 words** in ordinary replies and **250 words** when teaching.
- Review replies over **300 words**. Keep essential facts, conditions, and uncertainty.
- Use short paragraphs for explanations, bullets for distinct points, and numbers for steps.
- Define unfamiliar technical terms when they first appear.
- Give concise progress updates during work.

These preferences apply to **conversation replies**. Documents, emails, and other requested deliverables keep their own requirements. Code and logs do not count toward prose targets.

The [response skill](skills/plainspoken/SKILL.md) owns the full rules. The shared checker flags mechanical review signals; it cannot judge whether an answer is clear or complete.

## Setup

Choose your installation guide: [Codex](docs/setup/codex.md), [Claude Code](docs/setup/claude.md), or [Cursor](docs/setup/cursor.md).
See [shared requirements and the manual checker](docs/setup.md) before installation.

Plainspoken targets **Codex**, **Claude Code**, and **Cursor**. Ordinary ChatGPT and Claude chats are separate products and are not covered by these integrations.

Hooks can request a review after an answer. They cannot retract text already shown to you. The skill instructs the assistant to review its writing before sending it.

## Development

Use [AGENTS.md](AGENTS.md) for the contributor entry point. Follow [development setup and checks](docs/development.md) before proposing changes.

For installation problems, see [troubleshooting](docs/troubleshooting.md).

## License

[MIT](LICENSE). Copyright 2026 Nikolai Alexander.
