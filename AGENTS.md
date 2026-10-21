# Contributor entry

- When changing response behavior, read [skills/plainspoken/SKILL.md](skills/plainspoken/SKILL.md). Keep the rules canonical there.
- When changing the checker or a host adapter, inspect its tests and run the relevant checks in [development checks](docs/development.md#checks).
- When changing installation or host behavior, update [setup](docs/setup.md) and [troubleshooting](docs/troubleshooting.md). Verify host claims against current official documentation.
- Report synthetic checks and observed host runs separately. A fixture test does not prove the host loaded the plugin.
