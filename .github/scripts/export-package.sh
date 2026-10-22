#!/usr/bin/env bash
# Export the tracked files of one revision into a clean directory, verify the
# distributed file set, and record the payload digest.
# Usage: export-package.sh <revision> <output-dir>
# Writes <output-dir>/plainspoken-<sha>.tar, <output-dir>/package.json and the
# extracted tree under <output-dir>/export/.
set -euo pipefail

revision="$1"
out="$2"
sha=$(git rev-parse --verify "$revision^{commit}")
mkdir -p "$out/export"

# Files the hosts install. Tests and docs travel in the archive but are not required.
required=(
  .claude-plugin/plugin.json .claude-plugin/marketplace.json
  .codex-plugin/plugin.json .cursor-plugin/plugin.json .agents/plugins/marketplace.json
  hooks/hooks.json hooks/codex.json hooks/cursor.json
  scripts/hook.py scripts/check_response.py
  skills/plainspoken/SKILL.md rules/plainspoken.mdc assets/icon.svg
  LICENSE pyproject.toml
)

# git archive is reproducible for one commit and stores the commit id in the tar header.
tar="$out/plainspoken-$sha.tar"
git archive --format=tar --prefix=plainspoken/ "$sha" > "$tar"
tar -xf "$tar" -C "$out/export" --strip-components=1
for file in "${required[@]}"; do
  test -s "$out/export/$file" || { echo "Export of $sha lacks $file" >&2; exit 1; }
done

python3 - "$sha" "$tar" "$out/package.json" "${required[@]}" <<'EOF'
import hashlib, json, re, sys
from pathlib import Path
sha, tar, target, *required = sys.argv[1:]
version = re.search(r'^version = "([^"]+)"', Path(tar).parent.joinpath("export/pyproject.toml").read_text(), re.M)
Path(target).write_text(json.dumps({
    "sha": sha,
    "version": version.group(1) if version else None,
    "archive": Path(tar).name,
    "sha256": hashlib.sha256(Path(tar).read_bytes()).hexdigest(),
    "required_files": required,
}, indent=2) + "\n")
EOF
cat "$out/package.json"
