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
production scope on every commit. Tests and coverage remain separate checks.
See [pre-commit usage](https://pre-commit.com/#usage).

## Check changes in CI

The [PR Pre-Merge Check workflow](../.github/workflows/tests.yml) runs only on
pull requests targeting `main`. New PR commits replace older in-progress runs.
Branch pushes do not start a duplicate workflow.

Its five checks follow Nplet's PR structure:

- **Code Quality Check:** lock validation, formatting, lint, and types.
- **Linux Tests, Windows Tests, and MacOS Tests:** the full suite and per-platform
  80% coverage gate, using the Python version pinned in `.python-version`.
- **Test Quality Check:** requires all three platform jobs to pass, checks that
  each supplied evidence, then combines coverage and enforces the coverage floor.

Platform jobs retain coverage data, coverage XML, and test-result XML. The final
job retains combined coverage XML. This structure uses one pinned Python version;
the previous Python 3.11/3.14 matrix is no longer part of routine PR checks.

These are configured checks. A workflow file does not prove the jobs passed.
The test commands use Bash on all three systems, including Windows. They exercise
Python behavior and synthetic hook payloads. They do not establish native Windows
host integration or installed-plugin activation.

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
