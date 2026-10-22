"""Mark tests by tier from their directory, so test files need no pytest import.

The Python 3.11 runtime lane runs these files with unittest alone; pytest never
loads this file there.
"""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply the unit or integration marker from each test's parent directory."""
    for item in items:
        tier = item.path.parent.name
        if tier in ("unit", "integration"):
            item.add_marker(tier)
