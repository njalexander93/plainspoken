"""Check that the three host plugin manifests agree with each other and the files they reference.

These are JSON and file-existence checks. They do not validate a manifest against any host's
schema; see docs/development.md#verify-host-changes for host validation.
"""

import json
import re
import tomllib
import unittest
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
)
MARKETPLACES = (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json")


def _commands(node: object) -> Iterator[str]:
    """Yield every "command" string nested anywhere in a parsed hooks file."""
    if isinstance(node, dict):
        if isinstance(node.get("command"), str):
            yield node["command"]
        for value in node.values():
            yield from _commands(value)
    elif isinstance(node, list):
        for value in node:
            yield from _commands(value)


class ManifestTests(unittest.TestCase):
    """Verify manifest versions and referenced files without a host."""

    def test_manifest_versions_match_pyproject(self) -> None:
        """Require one version across pyproject and every host manifest."""
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
        expected = pyproject["project"]["version"]
        for manifest in MANIFESTS:
            with self.subTest(manifest=manifest):
                data = json.loads((ROOT / manifest).read_text())
                self.assertEqual(data["version"], expected)
                self.assertEqual(data["name"], pyproject["project"]["name"])

    def test_manifest_references_exist(self) -> None:
        """Resolve every path a manifest references relative to the repository root."""
        for manifest in MANIFESTS:
            data = json.loads((ROOT / manifest).read_text())
            paths = [
                data[key] for key in ("skills", "hooks", "rules", "icon", "logo") if key in data
            ]
            paths += [data["interface"]["logo"]] if "interface" in data else []
            for reference in paths:
                with self.subTest(manifest=manifest, reference=reference):
                    self.assertTrue((ROOT / reference).exists(), reference)
        self.assertTrue((ROOT / "skills/plainspoken/SKILL.md").is_file())
        self.assertTrue(list((ROOT / "rules").glob("*.mdc")))

    def test_hook_commands_reference_packaged_script(self) -> None:
        """Parse each hooks file and confirm its commands call the shipped hook script."""
        for manifest in MANIFESTS:
            hooks = json.loads(
                (ROOT / json.loads((ROOT / manifest).read_text())["hooks"]).read_text()
            )
            commands = list(_commands(hooks))
            self.assertTrue(commands, manifest)
            for command in commands:
                with self.subTest(manifest=manifest, command=command):
                    match = re.search(r'_PLUGIN_ROOT}/(scripts/[\w.]+)"', command)
                    self.assertIsNotNone(match, command)
                    assert match is not None
                    self.assertTrue((ROOT / match.group(1)).is_file())

    def test_marketplaces_point_at_this_plugin(self) -> None:
        """Parse each marketplace file and check it lists this plugin from the checkout root."""
        for marketplace in MARKETPLACES:
            with self.subTest(marketplace=marketplace):
                plugins = json.loads((ROOT / marketplace).read_text())["plugins"]
                self.assertEqual([plugin["name"] for plugin in plugins], ["plainspoken"])
                source = plugins[0]["source"]
                path = source if isinstance(source, str) else source["path"]
                self.assertEqual(path, "./")


if __name__ == "__main__":
    unittest.main()
