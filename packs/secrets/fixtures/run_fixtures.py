"""Run Secrets Pack fixture scenarios.

Usage:
    python packs/secrets/fixtures/run_fixtures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parents[2]))

import yaml
from activegraph import Graph, Runtime
from packs.core import pack as core_pack
from packs.secrets import pack as secrets_pack, SecretsSettings


def _run_fixture(name: str, scenario: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []

    graph = Graph()
    rt = Runtime(graph)
    rt.load_pack(core_pack)
    rt.load_pack(secrets_pack, settings=SecretsSettings(record_usage_events=True))

    for obj_spec in scenario.get("objects", []):
        graph.add_object(obj_spec["type"], obj_spec["data"])

    rt.run_until_idle()

    by_type: dict[str, list] = {}
    for o in graph.objects():
        by_type.setdefault(o.type, []).append(o)

    expected = scenario.get("expected_outputs", {})

    if "secret_usage_events" in expected:
        exp = expected["secret_usage_events"]
        events = by_type.get("secret_usage_event", [])
        count = len(events)
        if "min_count" in exp and count < exp["min_count"]:
            failures.append(f"  secret_usage_events: expected >= {exp['min_count']}, got {count}")
        if "each_has" in exp:
            for field in exp["each_has"]:
                missing = [e for e in events if not e.data.get(field)]
                if missing:
                    failures.append(f"  {len(missing)} secret_usage_event(s) missing '{field}'")

        print(f"  credential_ref objects: {len(by_type.get('credential_ref', []))}")
        print(f"  secret_usage_event objects: {count}")
        for e in events[:3]:
            print(f"    name={e.data.get('credential_ref_name')} timestamp={e.data.get('timestamp','?')[:19]}")

    return (len(failures) == 0), failures


def main():
    _HERE = Path(__file__).parent
    fixtures = sorted(_HERE.glob("*.yaml"))
    if not fixtures:
        print("No YAML fixtures found.")
        sys.exit(1)

    results = []
    for fpath in fixtures:
        scenario = yaml.safe_load(fpath.read_text())
        name = fpath.stem
        print(f"\n{'='*60}\nFixture: {name}\n{'='*60}")
        passed, failures = _run_fixture(name, scenario)
        results.append((name, passed))
        print("  PASS" if passed else f"  FAIL:")
        for f in failures:
            print(f)

    total = len(results)
    passed_count = sum(1 for _, ok in results if ok)
    print(f"\n{'='*60}\nResults: {passed_count}/{total} fixtures passed\n{'='*60}\n")
    if passed_count < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
