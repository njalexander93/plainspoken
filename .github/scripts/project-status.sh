#!/usr/bin/env bash
# Move the issue linked to a branch to a GitHub Project status, never backward.
# Usage: project-status.sh <branch-name> <status-name>
# Needs GH_TOKEN with project write access, PROJECT_OWNER, PROJECT_NUMBER, GITHUB_REPOSITORY.
set -euo pipefail

branch="$1"
target="$2"
owner="${PROJECT_OWNER:?set the PROJECT_OWNER repository variable}"
number="${PROJECT_NUMBER:?set the PROJECT_NUMBER repository variable}"
repo="${GITHUB_REPOSITORY:?}"

# Branch convention: issue-<n>-<slug>, optionally under one prefix such as
# claude/github-issue-<n>-<slug>. Any other name is ignored, never guessed.
if [[ "$branch" =~ ^([A-Za-z0-9_.-]+/)?(github-)?issue-([0-9]+)(-|$) ]]; then
  issue="${BASH_REMATCH[3]}"
else
  echo "Branch '$branch' names no issue; nothing to do."
  exit 0
fi

# Later statuses rank higher; a delayed or duplicate event cannot move an issue back.
order=("Todo" "In Progress" "In Review" "Merged" "Staging" "Done" "Released")
rank() {
  local i
  for i in "${!order[@]}"; do
    [[ "${order[$i]}" == "$1" ]] && { echo "$i"; return; }
  done
  echo -1
}

project_id=$(gh project view "$number" --owner "$owner" --format json | jq -r .id)
fields=$(gh project field-list "$number" --owner "$owner" --format json)
field_id=$(jq -r '.fields[] | select(.name == "Status") | .id' <<<"$fields")
option_id=$(jq -r --arg s "$target" \
  '.fields[] | select(.name == "Status") | .options[] | select(.name == $s) | .id' <<<"$fields")
if [[ -z "$field_id" || -z "$option_id" ]]; then
  echo "Project $number has no Status option named '$target'." >&2
  exit 1
fi

# item-add returns the existing item when the issue is already in the project.
item_id=$(gh project item-add "$number" --owner "$owner" \
  --url "https://github.com/$repo/issues/$issue" --format json | jq -r .id)
current=$(gh project item-list "$number" --owner "$owner" --format json --limit 1000 |
  jq -r --arg id "$item_id" '.items[] | select(.id == $id) | .status // ""')
if (( $(rank "$current") >= $(rank "$target") )); then
  echo "Issue #$issue is '$current'; not moving back to '$target'."
  exit 0
fi

gh project item-edit --project-id "$project_id" --id "$item_id" \
  --field-id "$field_id" --single-select-option-id "$option_id"
echo "Issue #$issue: '${current:-none}' -> '$target'."
