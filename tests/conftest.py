"""Shared pytest configuration and helpers for the activegraph-packs test suite.

All fixture tests run their corresponding pack script as a subprocess.
This matches how CI invokes fixtures and avoids import-order issues between
the activegraph runtime and the test collection phase.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def run_fixture_script(script_path: str) -> subprocess.CompletedProcess:
    """Run *script_path* (relative to REPO_ROOT) as a subprocess.

    Returns the CompletedProcess so the caller can inspect returncode,
    stdout, and stderr.
    """
    return subprocess.run(
        [sys.executable, script_path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def assert_fixture_passed(result: subprocess.CompletedProcess) -> None:
    """Assert that a fixture subprocess exited with code 0.

    On failure, include the last 3 000 chars of stdout and 500 chars of
    stderr so pytest's assertion output is self-contained.
    """
    if result.returncode != 0:
        tail_out = result.stdout[-3000:] if result.stdout else ""
        tail_err = result.stderr[-500:] if result.stderr else ""
        raise AssertionError(
            f"Fixture script exited with code {result.returncode}.\n"
            f"--- stdout (last 3000 chars) ---\n{tail_out}\n"
            f"--- stderr (last 500 chars) ---\n{tail_err}"
        )
