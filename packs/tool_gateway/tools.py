"""Tool Gateway Pack tools — v0.1.

Provides execute_capability: the main tool for dispatching a capability
call after policy approval. Returns a CapabilityResult dict.

The `@tool`-decorated object is registered in the pack for the runtime.
The raw function is exported as `execute_capability_fn` so Python code
can call it directly without going through the Tool wrapper.

In production, behaviors should NOT call execute_capability directly —
they should create a CapabilityCall object (proposed), let policy_enforcer
approve it, and then call execute_capability. This keeps all calls
graph-visible and policy-gated.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from activegraph.packs import tool


# ------------------------------------------------------------------ registry

# Registered local capability handlers:
#   "{provider_name}.{capability_name}" -> Callable
_LOCAL_REGISTRY: dict[str, Callable] = {}


def register_local_capability(provider_name: str, capability_name: str, fn: Callable):
    """Register a local Python function as a capability.

    The key is "{provider_name}.{capability_name}" (case-sensitive).

    Example:
        def my_lookup(company_name: str) -> dict:
            return {"company": company_name, "founded": 2021}

        register_local_capability("crm", "lookup_company", my_lookup)
    """
    key = f"{provider_name}.{capability_name}"
    _LOCAL_REGISTRY[key] = fn


# ------------------------------------------------------------------ raw function (callable directly)


def execute_capability_fn(
    provider_name: str,
    capability_name: str,
    input_data: dict[str, Any],
    call_id: str = "",
    frame_id: Optional[str] = None,
) -> dict[str, Any]:
    """Dispatch a capability call to the appropriate handler.

    Routes to:
    1. Local registry (registered Python functions)
    2. Falls back to a mock response for testing

    Real API/MCP/SDK adapters will be added in v0.2.

    Args:
        provider_name: Name of the capability provider
        capability_name: Name of the capability to invoke
        input_data: Input parameters (no secrets)
        call_id: ID of the CapabilityCall being executed
        frame_id: Optional frame scope

    Returns:
        Dict with: output_data (str), error (str|None),
                   success (bool), executed_at (str)
    """
    now = datetime.now(timezone.utc).isoformat()
    key = f"{provider_name}.{capability_name}"

    try:
        if key in _LOCAL_REGISTRY:
            result = _LOCAL_REGISTRY[key](**input_data)
            output_str = json.dumps(result) if not isinstance(result, str) else result
        else:
            # No handler registered — return a structured mock for testing
            output_str = json.dumps({
                "mock": True,
                "provider": provider_name,
                "capability": capability_name,
                "inputs": input_data,
                "note": f"No handler registered for '{key}'. Register via register_local_capability().",
            })

        return {
            "output_data": output_str,
            "error": None,
            "success": True,
            "executed_at": now,
        }

    except Exception as exc:
        return {
            "output_data": "",
            "error": f"{type(exc).__name__}: {exc}",
            "success": False,
            "executed_at": now,
        }


# ------------------------------------------------------------------ tool wrapper (for pack registration)


@tool(
    name="execute_capability",
    description=(
        "Execute an approved capability call and return the result. "
        "Call this ONLY after policy_enforcer has set status='approved'. "
        "Returns a dict with: output_data, error, success, executed_at."
    ),
)
def execute_capability(
    provider_name: str,
    capability_name: str,
    input_data: dict[str, Any],
    call_id: str = "",
    frame_id: Optional[str] = None,
) -> dict[str, Any]:
    """Registered tool wrapper — delegates to execute_capability_fn."""
    return execute_capability_fn(
        provider_name=provider_name,
        capability_name=capability_name,
        input_data=input_data,
        call_id=call_id,
        frame_id=frame_id,
    )


TOOLS = [execute_capability]
