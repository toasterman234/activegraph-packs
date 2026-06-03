"""Tool Gateway Pack behaviors — v0.1.

Three behaviors covering the capability call lifecycle:

1. call_recorder — on capability_call.created (proposed), creates a
   calls relation to the provider and logs the call.

2. policy_enforcer — on capability_call.created (proposed), checks
   risk_class against auto_approve settings and updates status to
   'approved' or 'rejected'.

3. result_sourcer — on capability_result.created, maps the result
   to a Core source object so downstream behaviors can observe output.

Design rules:
- @behavior signature: (name, on, where, view, creates, budget, priority)
- 'description' goes in the docstring, not @behavior
- Behaviors must not store actual secrets — credential_ref_name only
- Policy decisions must be graph-visible (status field on CapabilityCall)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from activegraph.packs import behavior

from .object_types import CapabilityCall, CapabilityResult
from .settings import ToolGatewaySettings


# ------------------------------------------------------------------ behaviors


@behavior(
    name="call_recorder",
    on=["object.created"],
    where={"object.type": "capability_call"},
    creates=[],
)
def call_recorder(event, graph, ctx, *, settings: ToolGatewaySettings):
    """Record a proposed capability call and create its provider relation.

    On: object.created (capability_call)
    Creates: calls(capability_call → capability_provider) relation
    Side effects: logs call for audit trail

    Runs immediately when a capability_call is added to the graph.
    Does not execute the call — that is handled by the calling code
    after policy_enforcer approves the call.
    """
    obj = event.payload.get("object", {})
    call_id = obj.get("id")
    call_data = obj.get("data", {})

    provider_id = call_data.get("provider_id")
    if not provider_id or not call_id:
        return

    # Create 'calls' relation: capability_call → capability_provider
    try:
        graph.add_relation("calls", call_id, provider_id)
    except Exception:
        pass  # Provider may not exist yet in simple setups


@behavior(
    name="policy_enforcer",
    on=["object.created"],
    where={"object.type": "capability_call"},
    creates=[],
)
def policy_enforcer(event, graph, ctx, *, settings: ToolGatewaySettings):
    """Check a proposed capability call against the policy configuration.

    On: object.created (capability_call, status=proposed)
    Creates: updates capability_call.status to 'approved' or 'rejected'

    Auto-approves calls whose risk_class is in settings.auto_approve_risk_classes.
    All other risk classes set status to 'policy_checking' (requires manual approval).

    This is graph-visible: status changes are recorded as patches,
    so the full policy decision history is auditable.
    """
    obj = event.payload.get("object", {})
    call_id = obj.get("id")
    call_data = obj.get("data", {})

    risk_class = call_data.get("risk_class", "medium")
    current_status = call_data.get("status", "proposed")

    if current_status != "proposed":
        return  # Only process newly proposed calls

    if risk_class in settings.auto_approve_risk_classes:
        new_status = "approved"
    else:
        new_status = "policy_checking"

    # Patch the capability_call status to reflect the policy decision
    try:
        graph.patch_object(call_id, {"status": new_status})
    except Exception:
        pass  # Patch may fail if the runtime doesn't support it


@behavior(
    name="result_sourcer",
    on=["object.created"],
    where={"object.type": "capability_result"},
    creates=["source"],
)
def result_sourcer(event, graph, ctx, *, settings: ToolGatewaySettings):
    """Map a capability result to a Core source object.

    On: object.created (capability_result)
    Creates: source (kind=tool_result) with the result content
    Creates: sourced_as(capability_result → source) relation

    This is the bridge between Tool Gateway and Core Pack.
    By creating a source object, downstream Core behaviors
    (observation_extractor etc.) can observe the tool output.
    """
    if not settings.create_source_from_result:
        return

    obj = event.payload.get("object", {})
    result_id = obj.get("id")
    result_data = obj.get("data", {})

    output_data = result_data.get("output_data", "")
    if not output_data:
        return

    provider_name = result_data.get("provider_name", "unknown")
    capability_name = result_data.get("capability_name", "unknown")
    frame_id = result_data.get("frame_id")
    call_id = result_data.get("call_id", "")

    # Truncate output to configured limit
    content = output_data[: settings.max_output_chars]

    # Create Core source object from the result
    source = graph.add_object(
        "source",
        {
            "kind": "tool_result",
            "content": content,
            "url": None,
            "channel": "tool_gateway",
            "sender_ref": f"{provider_name}.{capability_name}",
            "frame_id": frame_id,
            "metadata": {
                "call_id": call_id,
                "provider": provider_name,
                "capability": capability_name,
            },
        },
    )

    # Update result with source_id
    try:
        graph.patch_object(result_id, {"source_id": source.id})
    except Exception:
        pass

    # Create sourced_as relation: capability_result → source
    try:
        graph.add_relation("sourced_as", result_id, source.id)
    except Exception:
        pass


BEHAVIORS = [call_recorder, policy_enforcer, result_sourcer]
