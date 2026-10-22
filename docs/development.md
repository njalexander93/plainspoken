# Develop Plainspoken

**Use Poetry for contributor tools.** Plainspoken itself uses only Python's standard library.
The [installation guides](setup.md) do not require Poetry.

## Set up a checkout

The project accepts **Python 3.11 or newer**. Development uses **Python 3.14.8**
from [`.python-version`](../.python-version) and **Poetry 2.4.2**.
These pins define the reproducible development environment, not a narrower runtime requirement.

1. Install Python 3.14.8 and Poetry 2.4.2. See the official
   [Python downloads](https://www.python.org/downloads/) and
   [Poetry installation guide](https://python-poetry.org/docs/#installation).
2. From the repository root, select that interpreter and sync locked tools:

   ```sh
   poetry env use /absolute/path/to/python3.14
   poetry sync
   poetry run python --version
   ```

3. Run the [checks](#checks) before requesting review.

On Windows, pass the quoted path to `python.exe` to `poetry env use`.
[Poetry configuration](../poetry.toml) keeps `.venv/` inside the checkout.
Create a separate environment for each clone or worktree.

[`pyproject.toml`](../pyproject.toml) defines the tools. [`poetry.lock`](../poetry.lock)
pins their resolved dependencies. Commit both when dependencies change.
Use `poetry sync` to reproduce the lock. Run `poetry lock` only when deliberately
updating dependencies, then review the lock diff.

The project uses Poetry's non-package mode. Sync installs contributor dependencies
without building or installing Plainspoken as a Python package.
See [Poetry dependency management](https://python-poetry.org/docs/managing-dependencies/)
and [non-package mode](https://python-poetry.org/docs/basic-usage/#operating-modes).

## Checks

The full suite needs Bash and `python3` on `PATH`. Tests execute the shell commands
from the plugin manifests. On Windows, use Git Bash for these checks. This does
not establish native Windows host compatibility.

Run these commands from the repository root:

```sh
poetry check --lock --strict
poetry run ruff format --check .
poetry run ruff check --no-fix .
poetry run mypy
poetry run pytest tests/unit --cov --cov-report= --cov-fail-under=0 --junitxml=test-results-unit.xml
poetry run pytest tests/integration --cov --cov-append --cov-report=term-missing --cov-report=xml:coverage.xml --junitxml=test-results-integration.xml
```

- Ruff checks formatting, imports, lint rules, and Google-style docstrings.
- Mypy checks production Python under `scripts/`.
- Pytest runs two tiers, marked `unit` and `integration` from their directory by
  [`tests/conftest.py`](../tests/conftest.py). `tests/unit/` calls one module in process
  with its boundaries replaced. `tests/integration/` wires the real modules together,
  including the packaged hook commands as subprocesses, without a live host.
  Coverage includes branches and Python subprocesses under `scripts/`, with an 80%
  minimum over both tiers combined (`--cov-append`); the unit tier alone does not
  reach it because `scripts/hook.py` has no in-process test yet.
  Skipped tests print their reason (`-ra`). `pytest -m unit` selects one tier.
- [`tests/unit/test_manifests.py`](../tests/unit/test_manifests.py) checks that the three host manifests
  share `pyproject.toml`'s version, parse as JSON, and reference files that exist
  (hooks, skills, rules, scripts, assets). It does not validate any host's manifest schema;
  see [verify host changes](#verify-host-changes).
- The XML files contain coverage and test results. They are generated outputs, not source files.

To apply formatting explicitly, run `poetry run ruff format .`, then inspect the diff.
The runtime-only test command remains available without contributor dependencies:

```sh
python3 -m unittest discover -s tests/unit -t . -v
python3 -m unittest discover -s tests/integration -t . -v
```

That command does not replace lint, type checks, or coverage before review.

## Set up your editor

1. Open the checkout root in VS Code or Cursor. Install available extensions from
   [the recommendations](../.vscode/extensions.json).
2. Select the checkout's `.venv` Python interpreter. Sync Poetry first so the
   environment contains the pinned Ruff and mypy versions.
3. Use [the shared settings](../.vscode/settings.json). Python uses Ruff formatting,
   import organization, and lint fixes on explicit save. Mypy uses the project's
   `scripts/` scope. Pylance type checking is disabled to avoid a second type policy.

Ruff and mypy use `fromEnvironment`. Their extensions can fall back to bundled
tools if the environment lacks them. See the official
[Ruff import strategy](https://docs.astral.sh/ruff/editors/settings/#importstrategy)
and [mypy extension settings](https://github.com/microsoft/vscode-mypy#settings).

For other editors, apply [`.editorconfig`](../.editorconfig) with EditorConfig
support and select `.venv`. Use the Poetry commands above for checks.
The configuration is tracked. Live editor behavior has not been verified.

## Install local commit checks

Install the tracked [pre-commit configuration](../.pre-commit-config.yaml) after syncing the environment:

```sh
poetry run pre-commit install
poetry run pre-commit run --all-files
```

The configuration alone does not install a Git hook. The hooks check staged Python
formatting and lint without changing files. Mypy checks the full configured
production scope on every commit. Pytest then runs the unit tier and the
integration tier for the current OS, without coverage; tests for another OS skip
with a printed reason.
Coverage stays a CI check. Keep desktop E2E and model calls out of pre-commit.
See [pre-commit usage](https://pre-commit.com/#usage).

Observed on 2026-10-22 (macOS, Python 3.13): staging a file with an unused import and
unformatted code made `poetry run pre-commit run` report the Ruff format and lint
hooks as failed while Mypy and both test tiers passed. Pre-commit restores the working tree afterwards.

## Check changes in CI

The [PR Pre-Merge Check workflow](../.github/workflows/pr.yml) runs only on
pull requests targeting `main` when they are opened, reopened, or updated.
New PR commits cancel that PR's older in-progress run and nothing else.
Branch pushes do not start a duplicate workflow. The workflow also accepts
`workflow_call`, so release validation reuses these exact jobs.

Its six checks follow Nplet's PR structure:

- **Code Quality Check:** lock validation, formatting, lint, and types.
- **Linux Tests, Windows Tests, and MacOS Tests:** the unit tier, then the integration
  tier, as separate steps with separate test-result XML, and a per-platform 80%
  coverage gate over both, using the Python version pinned in `.python-version`.
  The suite has no OS-specific tests today; the Bash-dependent packaged-command test fails
  rather than skips when Bash is missing, and any skip prints its reason.
- **Python 3.11 Runtime Tests:** each tier through `python3 -m unittest discover`
  on the oldest promised runtime, without Poetry or the pinned contributor tools.
- **Test Quality Check:** requires all three platform jobs and the runtime lane to
  pass, checks that each platform supplied evidence, then combines coverage and
  enforces the coverage floor. A coverage percentage measures execution, not
  assertion quality.

Platform jobs retain coverage data, coverage XML, and test-result XML. The final
job retains combined coverage XML.

### Branch rules

Merge policy lives in the repository ruleset for `main`, not in workflow YAML.
As read on 2026-10-22, the ruleset requires these status checks, with
"require branches to be up to date" enabled: Code Quality Check, Linux Tests,
Windows Tests, MacOS Tests, and Test Quality Check. It also requires one approving
review with code-owner review, resolved threads, squash merges, and CodeQL.
Job names in `pr.yml` must keep matching those contexts. The runtime lane is
enforced through Test Quality Check, so no ruleset change is needed; adding
`Python 3.11 Runtime Tests` as a sixth required context is optional.

These are configured checks. A workflow file does not prove the jobs passed.
The test commands use Bash on all three systems, including Windows. They exercise
Python behavior and synthetic hook payloads. They do not establish native Windows
host integration or installed-plugin activation.

## Validate merges to main

The [Main Post-Merge Validation workflow](../.github/workflows/main.yml) runs on
every push to `main`: each merged PR, and any direct push the branch rules permit.
A PR that closes without merging starts nothing. Each run is bound to the pushed
commit: every job checks out `github.sha`, runs never cancel each other, and the
exported payload names that commit. A push to a `pilot/**` branch runs the same
validation, which is how the workflow is observed before it reaches `main`,
because GitHub cannot dispatch a workflow that is not yet on the default branch.
Once it is, `workflow_dispatch` on a tag revalidates an older revision.

Its jobs:

- **Merged Revision Checks:** `pr.yml` through `workflow_call`, unchanged, on the merged commit.
- **Package Export:** [`export-package.sh`](../.github/scripts/export-package.sh) exports
  the tracked files of the commit with `git archive` into a directory outside the
  checkout, verifies the files the host manifests need, records the archive's
  SHA-256 in `package.json`, and runs both test tiers from the export with Python 3.11
  and the standard library only. The export test that needs Git history skips there.
- **Claude Code CLI on Linux, Windows, and MacOS:** each job downloads that package,
  extracts it into a directory with spaces, installs a pinned Claude Code CLI with
  npm, and runs [`host_pilot_claude.py`](../.github/scripts/host_pilot_claude.py).
  The script launches `claude -p` from an empty directory with an empty
  `CLAUDE_CONFIG_DIR`, so only the exported plugin's hooks can run, and asserts the
  `system/init` plugin entry plus the `SessionStart` and `UserPromptSubmit`
  payloads from `--include-hook-events`. Exit status is not evidence: the adapter
  fails open and an unauthenticated session exits 1 after the hooks ran. With an
  `ANTHROPIC_API_KEY` repository secret, a second session asks for a long answer
  and asserts one `Stop` review request followed by an empty continuation response.
  Without the secret that session is recorded as skipped with its reason.
  `--bare` is not used: it loads the plugin but does not run its hooks (observed
  with Claude Code 2.1.296).
- **Release Eligibility:** runs unless cancelled, requires the three jobs above to
  succeed and all three host results to be present and passing, and writes
  `release-eligibility.json` with the commit, run URL, package digest, job results,
  and per-host checks. A missing host result fails it.
- **Project Status:** on a push to `main` only, after eligibility, moves linked
  issues as described in the next section.

Artifacts (`package`, `host-claude-*`, `release-eligibility`) are retained for 90
days, the maximum for this repository. The eligibility file and the package it
names are the handoff for the release workflow: publication must use exactly that
archive and digest. If they have expired, the revision is not eligible until a
`workflow_dispatch` run on a tag at that commit regenerates them. Publication
logic itself is not part of this workflow yet.

Limits, stated plainly:

- The host pilot drives the **Claude Code CLI**, not the Claude desktop app, Codex
  desktop, or Cursor. It verifies installation from the exported payload and
  callback delivery; it does not certify desktop behavior. Desktop and Codex/Cursor
  automation on GitHub-hosted runners has not been attempted yet; see the blockers
  recorded in the issue.
- Only trusted revisions run this workflow (pushes to `main` or a `pilot/**`
  branch, and manual dispatch, all of which need write access), so the API key
  never reaches PR code from a fork. Streams are
  retained as evidence; they contain the prompt, the answer, and the plugin path.
- Repeating the full validation for a version-only release merge is accepted.

## Track issue status on the GitHub Project

The [Project Status workflow](../.github/workflows/project-status.yml) moves the
linked issue on the GitHub Project through
[`project-status.sh`](../.github/scripts/project-status.sh):

- A branch named `issue-<n>-<slug>` is created on GitHub (first push included): **In Progress**.
  One prefix is also accepted, so `claude/github-issue-3-pr-checks` links issue 3.
  Any other name is ignored; the script never guesses from free text.
- A PR from such a branch targeting `main` is opened or reopened, draft included: **In Review**.
- That PR is merged: **Merged**. Closing without merging changes nothing.

Statuses only move forward in the order Todo, In Progress, In Review, Merged,
Staging, Done, Released, so delayed or duplicate events cannot move an issue back.
Events for one branch run serially. Any merged PR from an issue branch marks the
issue Merged, so give partial or unrelated work a branch without an issue number.

After [post-merge validation](#validate-merges-to-main) succeeds,
[`post-merge-status.sh`](../.github/scripts/post-merge-status.sh) looks up the PRs
whose merge commit is the validated commit and moves each linked issue:

- **Done** when every changed file is `README.md`, `LICENSE`, or a Markdown file under
  `docs/`. This is the reviewed nonfunctional allowlist.
- **Staging** for anything else, including `skills/plainspoken/SKILL.md`, hooks,
  workflows, packaging, and unknown paths. Staging means validated and awaiting
  release; it is not a hosted environment and not publication authorization.

Failed, cancelled, or incomplete validation never reaches this step, so the issue
stays Merged and the failed run is the evidence. Documentation-only merges still
run every check. A direct push has no PR and moves nothing. Released belongs to the
release workflow. The same token needs to read pull requests in this repository.

Setup, none of which is checked into the repository:

1. Create repository variables `PROJECT_OWNER` and `PROJECT_NUMBER` for the target Project.
2. Create a `PROJECT_TOKEN` secret with Project write access (a fine-grained token
   with `Projects: read and write`, or a classic token with the `project` scope).
   The default `GITHUB_TOKEN` cannot edit Projects.
3. Give the Project's Status field options named exactly as listed above.
4. Disable the Project's built-in "item closed → Done" workflow so closing keywords
   do not skip the post-merge stages. Issue open/closed state and Project Status are separate.

The workflow uses `pull_request_target` and checks out only the default branch, so
PR code never runs with the project token. A fork can still name a branch after an
issue; that moves a status, nothing more. The workflow was written against the
`gh project` CLI and has not yet been observed against a configured Project.

## Verify host changes

When changing host integration, validate its plugin manifests with the host and
exercise it in a disposable project. Record the host, version, operating system,
commands, and observed callbacks separately from synthetic tests.

The installation guides retain the observed host runs and their limits:
[Codex](setup/codex.md#observed-host-runs),
[Claude Code](setup/claude.md#observed-host-runs), and
[Cursor](setup/cursor.md#observed-host-runs).
A test fixture does not prove that a host loaded the plugin or improved an answer.

The earlier shared-code run on 2026-10-21 passed 23 tests locally on Python 3.13
and in Linux/macOS CI on Python 3.11. That historical result does not establish
the expanded matrix above.

See [AGENTS.md](../AGENTS.md) for contributor instructions.
