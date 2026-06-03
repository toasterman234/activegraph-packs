"""Agent Profile Pack behaviors — v0.1.

One behavior covering profile context assembly:

1. profile_context_provider — on profile_context_request.created,
   assembles a structured ProfileContextView from the referenced
   AgentProfile, Goals, StandingInstructions, PersonalityProfiles,
   and OwnerPreferences in the graph.

Design rules:
- graph.objects() is UNSAFE in behaviors — use get_object(id) instead
- ProfileContextRequest must carry profile_id for context assembly
- The behavior fetches the profile via graph.get_object(profile_id)
- Related objects (goals, instructions, preferences, personality) are
  stored in the local profile registry, updated by registration behaviors
- Context is filtered by channel and audience_role from the request
- External-facing views suppress mission (unless expose_mission_to_external)
- Instructions are sorted by priority (highest first), limited by settings

Registry pattern (same as Tool Gateway local registry):
  _PROFILE_REGISTRY[profile_id] = {
    "profile": {...},
    "goals": [...],
    "instructions": [...],
    "personality": [...],
    "preferences": [...],
  }

Populated by profile_registry_recorder (fires on all profile object types).
"""

from __future__ import annotations

from typing import Any

from activegraph.packs import behavior

from .object_types import ProfileContextView
from .settings import AgentProfileSettings


# ------------------------------------------------------------------ local registry
# Holds all profile-related objects indexed by profile_id.
# Behaviors read from this to assemble context without graph.objects().

_PROFILE_REGISTRY: dict[str, dict[str, Any]] = {}


def _get_or_create_profile_entry(profile_id: str) -> dict[str, Any]:
    if profile_id not in _PROFILE_REGISTRY:
        _PROFILE_REGISTRY[profile_id] = {
            "profile": {},
            "goals": [],
            "instructions": [],
            "personality": [],
            "preferences": [],
        }
    return _PROFILE_REGISTRY[profile_id]


def clear_profile_registry() -> None:
    """Clear the local profile registry. Used in fixture teardown."""
    _PROFILE_REGISTRY.clear()


# ------------------------------------------------------------------ behaviors


@behavior(
    name="profile_registry_recorder",
    on=["object.created"],
    where={"object.type": "agent_profile"},
    creates=[],
)
def profile_registry_recorder(event, graph, ctx, *, settings: AgentProfileSettings):
    """Index an AgentProfile in the local registry for fast lookup.

    On: object.created (agent_profile)
    Creates: nothing — updates local _PROFILE_REGISTRY

    This behavior runs whenever an AgentProfile is added to the graph.
    All related objects reference profile_id, so when profile_context_provider
    needs to assemble a view, it can find everything via the registry.
    """
    obj = event.payload.get("object", {})
    profile_id = obj.get("id")
    profile_data = obj.get("data", {})

    if not profile_id:
        return

    entry = _get_or_create_profile_entry(profile_id)
    entry["profile"] = {**profile_data, "id": profile_id}


@behavior(
    name="goal_registry_recorder",
    on=["object.created"],
    where={"object.type": "goal"},
    creates=[],
)
def goal_registry_recorder(event, graph, ctx, *, settings: AgentProfileSettings):
    """Index a Goal in the profile registry.

    On: object.created (goal)
    Creates: nothing — updates local _PROFILE_REGISTRY
    """
    obj = event.payload.get("object", {})
    goal_id = obj.get("id")
    goal_data = obj.get("data", {})

    profile_id = goal_data.get("profile_id", "")
    if not profile_id:
        return

    entry = _get_or_create_profile_entry(profile_id)
    entry["goals"].append({**goal_data, "id": goal_id})


@behavior(
    name="instruction_registry_recorder",
    on=["object.created"],
    where={"object.type": "standing_instruction"},
    creates=[],
)
def instruction_registry_recorder(event, graph, ctx, *, settings: AgentProfileSettings):
    """Index a StandingInstruction in the profile registry.

    On: object.created (standing_instruction)
    Creates: nothing — updates local _PROFILE_REGISTRY
    """
    obj = event.payload.get("object", {})
    instr_id = obj.get("id")
    instr_data = obj.get("data", {})

    profile_id = instr_data.get("profile_id", "")
    if not profile_id:
        return

    entry = _get_or_create_profile_entry(profile_id)
    entry["instructions"].append({**instr_data, "id": instr_id})


@behavior(
    name="personality_registry_recorder",
    on=["object.created"],
    where={"object.type": "personality_profile"},
    creates=[],
)
def personality_registry_recorder(event, graph, ctx, *, settings: AgentProfileSettings):
    """Index a PersonalityProfile in the profile registry.

    On: object.created (personality_profile)
    Creates: nothing — updates local _PROFILE_REGISTRY
    """
    obj = event.payload.get("object", {})
    obj_id = obj.get("id")
    obj_data = obj.get("data", {})

    profile_id = obj_data.get("profile_id", "")
    if not profile_id:
        return

    entry = _get_or_create_profile_entry(profile_id)
    entry["personality"].append({**obj_data, "id": obj_id})


@behavior(
    name="preference_registry_recorder",
    on=["object.created"],
    where={"object.type": "owner_preference"},
    creates=[],
)
def preference_registry_recorder(event, graph, ctx, *, settings: AgentProfileSettings):
    """Index an OwnerPreference in the profile registry.

    On: object.created (owner_preference)
    Creates: nothing — updates local _PROFILE_REGISTRY
    """
    obj = event.payload.get("object", {})
    obj_id = obj.get("id")
    obj_data = obj.get("data", {})

    profile_id = obj_data.get("profile_id", "")
    if not profile_id:
        return

    entry = _get_or_create_profile_entry(profile_id)
    entry["preferences"].append({**obj_data, "id": obj_id})


@behavior(
    name="profile_context_provider",
    on=["object.created"],
    where={"object.type": "profile_context_request"},
    creates=["profile_context_view"],
)
def profile_context_provider(event, graph, ctx, *, settings: AgentProfileSettings):
    """Assemble a scoped ProfileContextView from a ProfileContextRequest.

    On: object.created (profile_context_request)
    Creates: profile_context_view with filtered context
    Creates: fulfilled_by_profile(request → view) relation

    Fetches the AgentProfile via graph.get_object(profile_id).
    Uses the local registry for goals, instructions, preferences, and personality.
    Filters all context by channel and audience_role from the request.

    Owner-facing contexts include mission (unless expose_mission_to_external=False).
    External-facing contexts suppress mission by default.
    """
    obj = event.payload.get("object", {})
    request_id = obj.get("id")
    request_data = obj.get("data", {})

    profile_id = request_data.get("profile_id", "")
    if not profile_id:
        return

    channel = request_data.get("channel")
    audience_role = request_data.get("audience_role")
    include_goals = request_data.get("include_goals", True)
    include_preferences = request_data.get("include_preferences", True)
    frame_id = request_data.get("frame_id")

    is_external = audience_role in ("external", "customer", "unknown", None)

    # --- Fetch AgentProfile via get_object (safe in behaviors) ---
    profile_data: dict = {}
    try:
        profile_obj = graph.get_object(profile_id)
        if profile_obj:
            profile_data = profile_obj.data
    except Exception:
        pass

    # Fall back to registry if graph lookup fails
    registry_entry = _PROFILE_REGISTRY.get(profile_id, {})
    if not profile_data:
        profile_data = registry_entry.get("profile", {})

    agent_name = profile_data.get("name") or settings.default_agent_name
    mission = profile_data.get("mission") or settings.default_mission

    # Suppress mission from external audiences unless configured to expose
    if is_external and not settings.expose_mission_to_external:
        mission = ""

    # --- Personality (filter by channel and audience_role) ---
    personality_list = registry_entry.get("personality", [])
    personality: dict = {
        "tone": settings.default_tone,
        "verbosity": settings.default_verbosity,
        "formality": settings.default_formality,
    }
    for p in personality_list:
        p_channel = p.get("applies_to_channel")
        p_role = p.get("applies_to_audience_role")
        channel_ok = (p_channel is None) or (p_channel == channel)
        role_ok = (p_role is None) or (p_role == audience_role)
        if channel_ok and role_ok:
            personality = {
                "tone": p.get("tone", settings.default_tone),
                "verbosity": p.get("verbosity", settings.default_verbosity),
                "formality": p.get("formality", settings.default_formality),
            }
            break

    # --- Goals (filter by status=active, sort by priority) ---
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    active_goals: list[dict] = []
    if include_goals:
        all_goals = registry_entry.get("goals", [])
        active = [g for g in all_goals if g.get("status") == "active"]
        active.sort(key=lambda g: priority_order.get(g.get("priority", "medium"), 2))
        active_goals = active[: settings.max_active_goals]

    # --- Standing instructions (filter by channel + audience_role) ---
    all_instrs = registry_entry.get("instructions", [])
    matched_instrs = []
    for instr in all_instrs:
        if not instr.get("active", True):
            continue
        i_channel = instr.get("applies_to_channel")
        i_role = instr.get("applies_to_audience_role")
        channel_ok = (i_channel is None) or (i_channel == channel)
        role_ok = (i_role is None) or (i_role == audience_role)
        if channel_ok and role_ok:
            matched_instrs.append(instr)
    # Sort by priority (higher = more important, assembled first)
    matched_instrs.sort(key=lambda i: i.get("priority", 50), reverse=True)
    instruction_texts = [
        i.get("text", "") for i in matched_instrs[: settings.max_standing_instructions]
    ]

    # --- Owner preferences (filter by channel + domain) ---
    owner_prefs: dict[str, str] = {}
    if include_preferences:
        all_prefs = registry_entry.get("preferences", [])
        for pref in all_prefs:
            p_channel = pref.get("channel")
            channel_ok = (p_channel is None) or (p_channel == channel)
            if channel_ok:
                owner_prefs[pref.get("key", "")] = pref.get("value", "")

    # --- Assemble and store ProfileContextView ---
    view = graph.add_object(
        "profile_context_view",
        ProfileContextView(
            profile_id=profile_id,
            channel=channel,
            audience_role=audience_role,
            agent_name=agent_name,
            mission=mission,
            personality=personality,
            active_goals=active_goals,
            standing_instructions=instruction_texts,
            owner_preferences=owner_prefs,
            request_id=request_id,
            frame_id=frame_id,
            metadata={"assembled_by": "profile_context_provider"},
        ).model_dump(),
    )

    # Create fulfilled_by_profile relation
    try:
        graph.add_relation("fulfilled_by_profile", request_id, view.id)
    except Exception:
        pass


BEHAVIORS = [
    profile_registry_recorder,
    goal_registry_recorder,
    instruction_registry_recorder,
    personality_registry_recorder,
    preference_registry_recorder,
    profile_context_provider,
]
