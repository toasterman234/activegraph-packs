"""Run Memory Gateway Pack fixture scenarios.

Usage:
    python packs/memory_gateway/fixtures/run_fixtures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parents[2]))

import yaml
from activegraph import Graph, Runtime
from packs.core import pack as core_pack, CoreSettings
from packs.memory_gateway import pack as mg_pack, MemoryGatewaySettings
from packs.memory_gateway.backend import clear_all_backends


def _run_fixture(name: str, scenario: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []

    # Fresh backend for each fixture
    clear_all_backends()

    graph = Graph()
    rt = Runtime(graph)
    rt.load_pack(core_pack, settings=CoreSettings())
    rt.load_pack(mg_pack, settings=MemoryGatewaySettings(
        acceptance_threshold=0.6,
        auto_accept_categories=["preference", "instruction", "decision"],
    ))

    for obj_spec in scenario.get("objects", []):
        graph.add_object(obj_spec["type"], obj_spec["data"])

    rt.run_until_idle()

    by_type: dict[str, list] = {}
    for o in graph.objects():
        by_type.setdefault(o.type, []).append(o)

    all_relations = list(graph.relations())
    relation_types = {r.source for r in all_relations}

    expected = scenario.get("expected_outputs", {})

    # --- evaluations ---
    if "evaluations" in expected:
        exp = expected["evaluations"]
        evals = by_type.get("evaluation", [])
        count = len(evals)
        if "min_count" in exp and count < exp["min_count"]:
            failures.append(f"  evaluations: expected >= {exp['min_count']}, got {count}")

        if "has_accepted" in exp:
            accepted_evals = [e for e in evals if e.data.get("judgment") == "accepted"]
            min_acc = exp["has_accepted"].get("min_count", 1)
            if len(accepted_evals) < min_acc:
                failures.append(
                    f"  evaluations: expected >= {min_acc} accepted, got {len(accepted_evals)}"
                )

        print(f"  evaluations: {count} ({sum(1 for e in evals if e.data.get('judgment')=='accepted')} accepted, "
              f"{sum(1 for e in evals if e.data.get('judgment')=='rejected')} rejected)")

    # --- memory_items ---
    if "memory_items" in expected:
        exp = expected["memory_items"]
        items = by_type.get("memory_item", [])
        count = len(items)
        if "min_count" in exp and count < exp["min_count"]:
            failures.append(f"  memory_items: expected >= {exp['min_count']}, got {count}")
        print(f"  memory_items: {count}")
        for item in items[:3]:
            print(f"    [{item.data.get('confidence', 0):.2f}] {item.data.get('text','')[:60]}")

    # --- relations ---
    if "relations" in expected:
        for rel_spec in expected["relations"].get("includes", []):
            rtype = rel_spec["type"]
            if rtype not in relation_types:
                failures.append(
                    f"  relations: expected '{rtype}' ({rel_spec.get('description','')}), "
                    f"not found. Present: {sorted(relation_types)}"
                )

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
