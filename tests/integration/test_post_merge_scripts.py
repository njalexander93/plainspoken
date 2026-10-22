"""Exercise the post-merge shell scripts: package export and change classification."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".github/scripts"


class PostMergeScriptTests(unittest.TestCase):
    """Run the scripts through Bash as the workflow does."""

    def setUp(self) -> None:
        """Locate Bash, which the workflow and the packaged commands require."""
        self.bash = shutil.which("bash")
        self.assertIsNotNone(self.bash, "Post-merge script tests require Bash on PATH")

    def classify(self, *files: str) -> str:
        """Return the project status the script assigns to a set of changed files."""
        return subprocess.run(
            [self.bash, str(SCRIPTS / "post-merge-status.sh"), "classify", *files],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def test_only_reviewed_nonfunctional_paths_reach_done(self) -> None:
        """Send documentation-only changes to Done and everything else to Staging."""
        self.assertEqual(self.classify("README.md", "docs/setup/claude.md", "LICENSE"), "Done")
        for files in (
            [],
            ["README.md", "skills/plainspoken/SKILL.md"],
            ["docs/development.md", ".github/workflows/pr.yml"],
            ["docs/assets/diagram.svg"],
            ["unknown/file.md"],
        ):
            with self.subTest(files=files):
                self.assertEqual(self.classify(*files), "Staging")

    def test_export_matches_head_and_records_digest(self) -> None:
        """Export HEAD into a clean directory and check the recorded package identity."""
        if not (ROOT / ".git").exists():
            self.skipTest("The export has no Git history to export from")
        with tempfile.TemporaryDirectory(prefix="plainspoken export ") as directory:
            out = Path(directory) / "package"
            subprocess.run(
                [self.bash, str(SCRIPTS / "export-package.sh"), "HEAD", str(out)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            package = json.loads((out / "package.json").read_text())
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
            self.assertEqual(package["sha"], head)
            self.assertEqual(package["archive"], f"plainspoken-{head}.tar")
            self.assertEqual(len(package["sha256"]), 64)
            for required in package["required_files"]:
                self.assertTrue((out / "export" / required).is_file(), required)
            self.assertFalse((out / "export" / ".git").exists())


if __name__ == "__main__":
    unittest.main()
