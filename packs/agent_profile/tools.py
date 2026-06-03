"""Agent Profile Pack tools — v0.1.

Provides helpers for profile registration and context request creation.
"""

from __future__ import annotations

from typing import Any, Optional

from activegraph.packs import tool


# ------------------------------------------------------------------ raw functions


def register_profile_fn(
    graph: Any,
    name: str,
    mission: str = "",
    personality_description: str = "",
    owner_name: Optional[str] = None,
) -> Any:
    """Add an AgentProfile to the graph and return the created object.

    Triggers profile_registry_recorder behavior to index in local registry.

    Args:
        graph: ActiveGraph Graph instance
        name: Assistant name
        mission: Mission statement
        personality_description: Free-text personality description
        owner_name: Owner's name

    Returns:
        The created graph object.
    """
    return graph.add_object(
        "agent_profile",
        {
            "name": name,
            "mission": mission,
            "personality_description": personality_description,
            "owner_name": owner_name,
            "version": "1",
            "active": True,
            "metadata": {},
        },
    )


def request_profile_context_fn(
    graph: Any,
    profile_id: str,
    channel: Optional[str] = None,
    audience_role: Optional[str] = None,
    frame_id: Optional[str] = None,
    include_goals: bool = True,
    include_preferences: bool = True,
) -> Any:
    """Create a ProfileContextRequest to trigger context assembly.

    profile_context_provider behavior fires and creates a ProfileContextView.
    Call rt.run_until_idle() after this to get the assembled view.

    Returns:
        The ProfileContextRequest graph object.
    """
    return graph.add_object(
        "profile_context_request",
        {
            "profile_id": profile_id,
            "channel": channel,
            "audience_role": audience_role,
            "include_goals": include_goals,
            "include_preferences": include_preferences,
            "frame_id": frame_id,
            "metadata": {},
        },
    )


# ------------------------------------------------------------------ tool wrappers


@tool(
    name="register_profile",
    description=(
        "Register an AgentProfile in the graph. "
        "Triggers profile_registry_recorder to index it for context assembly. "
        "Returns the created profile object."
    ),
)
def register_profile(
    graph: Any,
    name: str,
    mission: str = "",
    personality_description: str = "",
    owner_name: Optional[str] = None,
) -> Any:
    """Registered tool wrapper."""
    return register_profile_fn(graph, name, mission, personality_description, owner_name)


@tool(
    name="request_profile_context",
    description=(
        "Create a ProfileContextRequest to assemble a scoped context view. "
        "Triggers profile_context_provider behavior. "
        "Call rt.run_until_idle() after to read the ProfileContextView."
    ),
)
def request_profile_context(
    graph: Any,
    profile_id: str,
    channel: Optional[str] = None,
    audience_role: Optional[str] = None,
    frame_id: Optional[str] = None,
) -> Any:
    """Registered tool wrapper."""
    return request_profile_context_fn(graph, profile_id, channel, audience_role, frame_id)


TOOLS = [register_profile, request_profile_context]
