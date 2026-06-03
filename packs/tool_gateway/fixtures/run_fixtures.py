"""Run Tool Gateway Pack fixture scenarios.

Usage:
    python packs/tool_gateway/fixtures/run_fixtures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parents[2]))

import yaml
from activegraph import Graph, Runtime
from packs.core import pack as core_pack, CoreSettings
from packs.tool_gateway import pack as tg_pack, ToolGatewaySettings
from packs.tool_gateway.tools import register_local_capability


def _run_fixture(name: str, scenario: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []

    graph = Graph()
    rt = Runtime(graph)
    rt.load_pack(core_pack, settings=CoreSettings())
    rt.load_pack(tg_pack, settings=ToolGatewaySettings(
        auto_approve_risk_classes=["low", "medium"],
    ))

    # Register a mock local capability
    register_local_capability("CRM API", "lookup_company", lambda company_name="": {
        "company": company_name, "founded": 2021, "arr": "$2.4M"
    })

    # Create declared objects, capture first provider id for placeholder
    created_ids: dict[str, list[str]] = {}
    for obj_spec in scenario.get("objects", []):
        obj_type = obj_spec["type"]
        obj_data = dict(obj_spec["data"])

        # Resolve PLACEHOLDER_PROVIDER_ID
        if "provider_id" in obj_data and obj_data["provider_id"] == "PLACEHOLDER_PROVIDER_ID":
            if created_ids.get("capability_provider"):
                obj_data["provider_id"] = created_ids["capability_provider"][0]

        obj = graph.add_object(obj_type, obj_data)
        created_ids.setdefault(obj_type, []).append(obj.id)

    rt.run_until_idle()

    # Gather state
    all_relations = list(graph.relations())
    relation_types = {r.source for r in all_relations}

    expected = scenario.get("expected_outputs", {})
    if "relations" in expected:
        for rel_spec in expected["relations"].get("includes", []):
            rtype = rel_spec["type"]
            if rtype not in relation_types:
                failures.append(
                    f"  relations: expected '{rtype}' ({rel_spec.get('description','')}), "
                    f"not found. Present: {sorted(relation_types)}"
                )

    # Also verify we created the expected object types
    for obj_type in ["capability_provider", "capability_call"]:
        objs = list(graph.objects(type=obj_type))
        if not objs:
            failures.append(f"  Expected {obj_type} objects, none found")
        else:
            print(f"  {obj_type}: {len(objs)} object(s)")
            for o in objs[:2]:
                print(f"    status={o.data.get('status', 'n/a')} name={o.data.get('name', o.data.get('capability_name', ''))}")

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
        if passed:
            print("  PASS")
        else:
            print(f"  FAIL — {len(failures)} failure(s):")
            for f in failures:
                print(f)

    total = len(results)
    passed_count = sum(1 for _, ok in results if ok)
    print(f"\n{'='*60}\nResults: {passed_count}/{total} fixtures passed\n{'='*60}\n")
    if passed_count < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
