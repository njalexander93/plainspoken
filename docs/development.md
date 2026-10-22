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
poetry run pytest --cov --cov-report=term-missing --cov-report=xml:coverage.xml --junitxml=test-results.xml
```

- Ruff checks formatting, imports, lint rules, and Google-style docstrings.
- Mypy checks production Python under `scripts/`.
- Pytest runs the existing tests. Coverage includes branches and Python subprocesses under `scripts/`, with an 80% minimum.
  Skipped tests print their reason (`-ra`).
- [`tests/test_manifests.py`](../tests/test_manifests.py) checks that the three host manifests
  share `pyproject.toml`'s version, parse as JSON, and reference files that exist
  (hooks, skills, rules, scripts, assets). It does not validate any host's manifest schema;
  see [verify host changes](#verify-host-changes).
- The XML files contain coverage and test results. They are generated outputs, not source files.

To apply formatting explicitly, run `poetry run ruff format .`, then inspect the diff.
The runtime-only test command remains available without contributor dependencies:

```sh
python3 -m unittest discover -s tests -v
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
production scope on every commit. Pytest runs the shared suite plus any test
for the current OS, without coverage; tests for another OS skip with a printed reason.
Coverage stays a CI check. Keep desktop E2E and model calls out of pre-commit.
See [pre-commit usage](https://pre-commit.com/#usage).

Observed on 2026-10-22 (macOS, Python 3.13): staging a file with an unused import and
unformatted code made `poetry run pre-commit run` report the Ruff format and lint
hooks as failed while Mypy and Pytest passed. Pre-commit restores the working tree afterwards.

## Check changes in CI

The [PR Pre-Merge Check workflow](../.github/workflows/pr.yml) runs only on
pull requests targeting `main` when they are opened, reopened, or updated.
New PR commits cancel that PR's older in-progress run and nothing else.
Branch pushes do not start a duplicate workflow. The workflow also accepts
`workflow_call`, so release validation reuses these exact jobs.

Its six checks follow Nplet's PR structure:

- **Code Quality Check:** lock validation, formatting, lint, and types.
- **Linux Tests, Windows Tests, and MacOS Tests:** the full suite and per-platform
  80% coverage gate, using the Python version pinned in `.python-version`.
  The suite has no OS-specific tests today; the Bash-dependent packaged-command test fails
  rather than skips when Bash is missing, and any skip prints its reason.
- **Python 3.11 Runtime Tests:** `python3 -m unittest discover -s tests` on the
  oldest promised runtime, without Poetry or the pinned contributor tools.
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
Staging, Done, and Released transitions belong to the post-merge and release workflows.

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
