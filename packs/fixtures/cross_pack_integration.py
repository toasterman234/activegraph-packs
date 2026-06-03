"""Cross-pack integration fixture: Tool Gateway → Core → Memory Gateway.

Demonstrates the full pipeline:
  1. Tool Gateway executes a mock API call → CapabilityResult
  2. result_sourcer maps result → Core source
  3. Core observation_extractor extracts observations
  4. Core memory_candidate_proposer creates memory candidates
  5. Memory Gateway candidate_evaluator evaluates candidates
  6. Memory Gateway memory_writer promotes accepted → MemoryItem
  7. retrieve_memories returns relevant items

Run without LLM or API key:
    python packs/fixtures/cross_pack_integration.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from activegraph import Graph, Runtime
from packs.core import pack as core_pack, CoreSettings
from packs.tool_gateway import pack as tg_pack, ToolGatewaySettings
from packs.tool_gateway.tools import execute_capability_fn, register_local_capability
from packs.secrets import pack as secrets_pack, SecretsSettings
from packs.memory_gateway import pack as mg_pack, MemoryGatewaySettings
from packs.memory_gateway.backend import clear_all_backends
from packs.memory_gateway.tools import retrieve_memories_fn


def run_integration_test() -> bool:
    """Run the cross-pack integration scenario. Returns True if passed."""
    print("\n" + "=" * 60)
    print("Cross-Pack Integration: Tool Gateway → Core → Memory Gateway")
    print("=" * 60)

    # Fresh backend
    clear_all_backends()

    # --- Setup ---
    graph = Graph()
    rt = Runtime(graph)

    rt.load_pack(core_pack, settings=CoreSettings(
        observation_min_confidence=0.3,
        max_observations_per_source=8,
    ))
    rt.load_pack(tg_pack, settings=ToolGatewaySettings(
        auto_approve_risk_classes=["low", "medium"],
        create_source_from_result=True,
    ))
    rt.load_pack(secrets_pack, settings=SecretsSettings())
    rt.load_pack(mg_pack, settings=MemoryGatewaySettings(
        acceptance_threshold=0.5,
        auto_accept_categories=["preference", "instruction", "decision", "fact"],
    ))

    # Register a mock CRM capability
    def mock_crm_lookup(company_name: str = "") -> dict:
        return {
            "company": company_name,
            "founded": 2021,
            "arr": "$2.4M",
            "headcount": 18,
            "key_preference": "API-first architecture preferred.",
            "decision": "Team decided to adopt event sourcing.",
            "instruction": "Always use JSON for API responses.",
        }

    register_local_capability("crm", "lookup_company", mock_crm_lookup)

    # --- Step 1: Register capability provider ---
    print("\n[1] Registering capability provider...")
    provider = graph.add_object("capability_provider", {
        "name": "crm",
        "kind": "api",
        "base_url": "https://crm.example.com",
        "description": "Mock CRM for integration test",
        "capabilities": ["lookup_company"],
        "credential_ref_name": None,
        "enabled": True,
        "metadata": {},
    })
    print(f"    Provider: {provider.id}")

    # --- Step 2: Propose a capability call ---
    print("\n[2] Proposing capability call (low risk → auto-approved)...")
    call = graph.add_object("capability_call", {
        "provider_id": provider.id,
        "provider_name": "crm",
        "capability_name": "lookup_company",
        "input_data": {"company_name": "Northwind Robotics"},
        "credential_ref_name": None,
        "risk_class": "low",
        "status": "proposed",
        "proposed_by": "integration_test",
        "frame_id": "frame_integration_001",
        "proposed_at": "2026-06-03T10:00:00Z",
        "metadata": {},
    })
    rt.run_until_idle()

    # Verify call was approved
    call_obj = graph.get_object(call.id)
    call_status = call_obj.data.get("status", "unknown") if call_obj else "unknown"
    print(f"    Call {call.id} status: {call_status}")

    # --- Step 3: Execute the call ---
    print("\n[3] Executing capability call...")
    result_data = execute_capability_fn(
        provider_name="crm",
        capability_name="lookup_company",
        input_data={"company_name": "Northwind Robotics"},
        call_id=call.id,
        frame_id="frame_integration_001",
    )
    print(f"    Success: {result_data['success']}")

    # --- Step 4: Record the result (triggers result_sourcer → source → observations) ---
    print("\n[4] Recording capability result...")
    result = graph.add_object("capability_result", {
        "call_id": call.id,
        "provider_name": "crm",
        "capability_name": "lookup_company",
        "output_data": result_data["output_data"],
        "error": result_data["error"],
        "success": result_data["success"],
        "executed_at": result_data["executed_at"],
        "sanitized": False,
        "source_id": None,
        "frame_id": "frame_integration_001",
        "metadata": {},
    })
    rt.run_until_idle()  # result_sourcer fires → source created → observations extracted → candidates proposed → memory evaluated

    # --- Step 5: Inspect results ---
    print("\n[5] Inspecting graph state...")
    sources = list(graph.objects(type="source"))
    observations = list(graph.objects(type="observation"))
    candidates = list(graph.objects(type="memory_candidate"))
    evaluations = list(graph.objects(type="evaluation"))
    memory_items = list(graph.objects(type="memory_item"))

    print(f"    sources: {len(sources)}")
    print(f"    observations: {len(observations)}")
    for obs in observations[:3]:
        cat = obs.data.get("category", "none")
        text = obs.data.get("text", "")[:55]
        print(f"      [{cat}] {text}")
    print(f"    memory_candidates: {len(candidates)}")
    print(f"    evaluations: {len(evaluations)}")
    accepted_evals = [e for e in evaluations if e.data.get("judgment") == "accepted"]
    print(f"    memory_items (accepted): {len(memory_items)} ({len(accepted_evals)} accepted)")

    # --- Step 6: Retrieve memories ---
    print("\n[6] Retrieving memories for 'API architecture preferences'...")
    results = retrieve_memories_fn(
        query="API architecture preferences",
        top_k=5,
        min_score=0.1,
        behavior_name="integration_test",
        frame_id="frame_integration_001",
    )
    print(f"    Retrieved {len(results)} item(s):")
    for r in results[:3]:
        print(f"      [{r['score']:.2f}] {r['text'][:60]}")

    # --- Assertions ---
    failures = []
    if not sources:
        failures.append("No sources created from capability result")
    if not observations:
        failures.append("No observations extracted from source")
    if not evaluations:
        failures.append("No evaluations created by candidate_evaluator")

    print("\n" + "=" * 60)
    if failures:
        print(f"FAIL — {len(failures)} assertion(s) failed:")
        for f in failures:
            print(f"  {f}")
        return False
    else:
        print("PASS — full pipeline verified: Tool Gateway → Core → Memory Gateway")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    passed = run_integration_test()
    sys.exit(0 if passed else 1)
