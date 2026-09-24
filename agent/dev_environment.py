"""Read-only development environment checks, shared by local launchers.

Only the standard library is imported so missing Agent dependencies can be
reported before importing MaaFramework or registering Custom callbacks.
The release entrypoint deliberately does not depend on this module.
"""

import json
import operator
import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def validate_environment() -> str:
    """Validate the active interpreter against the source manifest."""
    manifest = PROJECT_ROOT / "maa-project.json"
    try:
        project = json.loads(manifest.read_text(encoding="utf-8"))
        requires_python = project["python"]["requiresPython"]
        expected_maafw = project["maafw"]["version"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"Cannot read development requirements from {manifest}: {error}") from error
    if not isinstance(requires_python, str) or not isinstance(expected_maafw, str):
        raise ValueError(f"Invalid Python or MaaFramework requirements in {manifest}")

    comparisons = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "==": operator.eq}
    for bound in requires_python.split(","):
        match = re.fullmatch(r"(>=|<=|>|<|==)([0-9]+(?:\.[0-9]+){0,2})", bound.strip())
        if match is None:
            raise ValueError(f"Unsupported python.requiresPython constraint: {bound!r}")
        required = tuple(map(int, match[2].split(".")))
        if not comparisons[match[1]](sys.version_info[: len(required)], required):
            raise ValueError(f"Python {sys.version.split()[0]} does not satisfy {requires_python}.")

    try:
        actual_maafw = version("maafw")
    except PackageNotFoundError as error:
        raise ValueError("The selected Python environment does not have maafw installed.") from error
    if actual_maafw != expected_maafw:
        raise ValueError(f"maafw version mismatch: installed {actual_maafw}; required {expected_maafw}.")
    return actual_maafw


def check_environment(*, verbose: bool = False) -> bool:
    """Report bootstrap errors without importing unavailable Custom dependencies."""
    python = os.path.abspath(sys.executable)
    try:
        maafw_version = validate_environment()
    except ValueError as error:
        # Prompter itself imports maa; bootstrap failures must remain stdlib-only.
        print(f"Agent development environment check failed: {error}\nPython: {python}", file=sys.stderr)
        print(f"Run uv sync --frozen in {PROJECT_ROOT}, then restart the Agent.", file=sys.stderr)
        return False
    if verbose:
        print(f"Source: {PROJECT_ROOT}\nPython: {python}\nPython version: {sys.version.split()[0]}")
        print(f"maafw: {maafw_version}\nDevelopment environment ready.")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if check_environment(verbose=True) else 1)
