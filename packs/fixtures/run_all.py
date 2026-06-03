"""Run all cross-pack integration fixtures and report results.

Each fixture is run as a separate subprocess, matching how CI invokes them.
Exit code 0 = all pass, 1 = any fail.

Usage:
    python packs/fixtures/run_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]

FIXTURES = [
    (
        "Tool Gateway → Core → Memory Gateway",
        "packs/fixtures/cross_pack_integration.py",
    ),
    (
        "Communication + Chat + Email + Identity + Core",
        "packs/fixtures/comm_chat_email_integration.py",
    ),
    (
        "Identity/Auth + Agent Profile + Entity + Core",
        "packs/fixtures/identity_profile_entity_integration.py",
    ),
]


def run_fixture(label: str, script: str) -> bool:
    """Run a single fixture script as a subprocess. Returns True on pass."""
    result = subprocess.run(
        [sys.executable, script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    status = "PASS" if passed else "FAIL"
    print(f"  {status}  {label}")
    if not passed:
        for line in result.stdout.splitlines()[-15:]:
            print(f"        {line}")
        for line in result.stderr.splitlines()[-5:]:
            print(f"        {line}")
    return passed


def main() -> int:
    print()
    print("=" * 65)
    print("Cross-Pack Integration Fixtures")
    print("=" * 65)
    print()

    results = []
    for i, (label, script) in enumerate(FIXTURES, 1):
        print(f"[{i}] {label}")
        results.append(run_fixture(label, script))
        print()

    print("=" * 65)
    passed = sum(results)
    total = len(results)
    failed = total - passed

    if failed == 0:
        print(f"ALL PASSED ({passed}/{total})")
        print("=" * 65)
        return 0
    else:
        print(f"FAILED {failed}/{total} fixture(s)")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    sys.exit(main())
