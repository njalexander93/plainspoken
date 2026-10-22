#!/usr/bin/env bash
# After post-merge validation passes, move the issue linked to each PR merged as
# this commit to Done (nonfunctional change) or Staging (everything else).
# Usage: post-merge-status.sh classify <changed-file>...   prints Done or Staging
#        post-merge-status.sh apply <merge-commit-sha>
# apply needs GH_TOKEN, PROJECT_OWNER, PROJECT_NUMBER and GITHUB_REPOSITORY.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

classify() {
  # Reviewed allowlist of paths that cannot change product, packaging or delivery
  # behavior. Any other path, including skills, hooks and workflows, is functional.
  (($#)) || { echo Staging; return; }
  local file
  for file in "$@"; do
    case "$file" in
      README.md | LICENSE | docs/*.md) ;;
      *) echo Staging; return ;;
    esac
  done
  echo Done
}

case "$1" in
  classify)
    shift
    classify "$@"
    ;;
  apply)
    sha="$2"
    repo="${GITHUB_REPOSITORY:?}"
    # Only PRs whose merge produced exactly this commit; a direct push lists none.
    gh api "repos/$repo/commits/$sha/pulls" --jq \
      ".[] | select(.merged_at != null and .merge_commit_sha == \"$sha\") | \"\(.number) \(.head.ref)\"" |
      while read -r number branch; do
        mapfile -t files < <(gh api --paginate "repos/$repo/pulls/$number/files" --jq '.[].filename')
        target=$(classify "${files[@]}")
        echo "PR #$number ($branch): ${#files[@]} changed files -> $target"
        bash "$here/project-status.sh" "$branch" "$target"
      done
    ;;
  *)
    echo "Usage: $0 classify <file>... | apply <sha>" >&2
    exit 2
    ;;
esac
