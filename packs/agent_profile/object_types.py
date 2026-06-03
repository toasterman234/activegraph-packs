"""Agent Profile Pack object and relation types — v0.1.

Owns the assistant's goals, personality, style, and standing instructions.
Provides behavior-scoped context (not a global system prompt blob).

Object types:
  agent_profile        — The assistant's name, mission, personality description
  goal                 — A standing goal with priority, status, and domain
  standing_instruction — A scoped instruction (channel + audience_role filters)
  personality_profile  — Tone, verbosity, and formality settings
  owner_preference     — A named key/value preference from the owner
  profile_context_view — Assembled context view for a frame/channel/role

Design rules:
  - No global system prompt blobs — context is scoped per behavior
  - Standing instructions filter by channel and audience_role
  - Owner-facing and external-facing frames get different context slices
  - ProfileContextRequest → profile_context_provider → ProfileContextView
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ================================================================ Schemas


class AgentProfile(BaseModel):
    """The assistant's core identity: name, mission, and personality description.

    This is the root profile object. There should typically be one per agent.
    Loading a second AgentProfile overrides the first in profile views.
    """

    name: str = Field(description="The assistant's name.")
    mission: str = Field(
        default="",
        description="The assistant's mission statement (1–3 sentences).",
    )
    personality_description: str = Field(
        default="",
        description=(
            "Free-text description of the assistant's personality. "
            "E.g. 'Direct, analytical, and candid. Respects the owner's time.'"
        ),
    )
    owner_name: Optional[str] = Field(
        default=None,
        description="Name of the owner this assistant serves.",
    )
    version: str = Field(default="1", description="Profile version string.")
    active: bool = Field(default=True, description="Whether this profile is the active one.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Goal(BaseModel):
    """A standing goal the assistant is working toward.

    Goals are persistent (not per-turn). They inform which tasks and
    observations are relevant, and shape prioritization.
    """

    text: str = Field(description="Goal statement (one clear sentence).")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Goal priority for context ranking.",
    )
    status: Literal["active", "paused", "completed", "cancelled"] = Field(
        default="active",
        description="Current goal lifecycle status.",
    )
    domain: Optional[str] = Field(
        default=None,
        description=(
            "Goal domain for filtering (e.g. 'fundraising', 'product', "
            "'operations', 'personal')."
        ),
    )
    profile_id: Optional[str] = Field(
        default=None,
        description="ID of the AgentProfile this goal belongs to.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class StandingInstruction(BaseModel):
    """A standing instruction that applies to the assistant's behavior.

    Instructions can be scoped by channel and audience_role so the
    assistant behaves differently when talking to the owner vs. external
    contacts, or on email vs. chat.

    Examples:
    - 'Always reply in the language the user is writing in.'
    - 'When writing to investors, be concise and data-driven.'
    - 'Never reveal internal financials to external contacts.'
    """

    text: str = Field(description="The instruction text.")
    scope: str = Field(
        default="global",
        description=(
            "Scope this instruction applies to. "
            "Suggested: global, communication, memory, research, execution."
        ),
    )
    applies_to_channel: Optional[str] = Field(
        default=None,
        description=(
            "Channel filter. None = all channels. "
            "E.g. 'email', 'chat', 'sms', 'api'."
        ),
    )
    applies_to_audience_role: Optional[str] = Field(
        default=None,
        description=(
            "Audience role filter. None = all roles. "
            "E.g. 'owner', 'external', 'customer', 'collaborator'."
        ),
    )
    priority: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Instruction priority (higher = more important, assembled first).",
    )
    active: bool = Field(default=True, description="Whether this instruction is active.")
    profile_id: Optional[str] = Field(
        default=None,
        description="ID of the AgentProfile this instruction belongs to.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class PersonalityProfile(BaseModel):
    """Fine-grained personality settings: tone, verbosity, and formality.

    These settings parameterize the assistant's communication style.
    Scoped per profile and optionally per channel.
    """

    tone: Literal["neutral", "warm", "direct", "formal", "casual", "technical"] = Field(
        default="neutral",
        description="Default communication tone.",
    )
    verbosity: Literal["concise", "balanced", "detailed"] = Field(
        default="balanced",
        description="How much detail to include in responses.",
    )
    formality: Literal["informal", "neutral", "formal"] = Field(
        default="neutral",
        description="Formality level.",
    )
    applies_to_channel: Optional[str] = Field(
        default=None,
        description="Channel this personality applies to. None = all channels.",
    )
    applies_to_audience_role: Optional[str] = Field(
        default=None,
        description="Audience role this personality applies to. None = all roles.",
    )
    profile_id: Optional[str] = Field(
        default=None,
        description="ID of the AgentProfile this personality belongs to.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class OwnerPreference(BaseModel):
    """A named key/value preference set by the owner.

    Preferences are persistent and domain-scoped. They inform behavior
    across sessions (e.g., 'preferred_language: Spanish',
    'email_sign_off: Best, Alice').
    """

    key: str = Field(description="Preference key (e.g. 'preferred_language', 'email_sign_off').")
    value: str = Field(description="Preference value (always a string).")
    domain: Optional[str] = Field(
        default=None,
        description="Domain filter (e.g. 'email', 'research', 'global').",
    )
    channel: Optional[str] = Field(
        default=None,
        description="Channel filter (e.g. 'email', 'chat'). None = all channels.",
    )
    profile_id: Optional[str] = Field(
        default=None,
        description="ID of the AgentProfile this preference belongs to.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProfileContextRequest(BaseModel):
    """Request to assemble a scoped profile context view.

    Triggers profile_context_provider behavior. Caller supplies the
    profile_id and the channel/audience_role to filter context by.

    Pattern mirrors MemoryRetrievalRequest — graph-visible trigger.
    """

    profile_id: str = Field(description="ID of the AgentProfile graph object to assemble from.")
    channel: Optional[str] = Field(
        default=None,
        description="Channel to filter standing instructions and personality by.",
    )
    audience_role: Optional[str] = Field(
        default=None,
        description="Audience role to filter standing instructions by.",
    )
    include_goals: bool = Field(default=True, description="Include active goals in the view.")
    include_preferences: bool = Field(default=True, description="Include owner preferences.")
    frame_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProfileContextView(BaseModel):
    """Assembled profile context for a specific channel/audience_role.

    Created by profile_context_provider in response to a
    ProfileContextRequest. Contains the profile slice appropriate
    for the requested channel and audience role.

    Design: structured dict, not a raw string blob, so behaviors
    can select only the fields they need.
    """

    profile_id: str = Field(description="Source profile ID.")
    channel: Optional[str] = Field(default=None)
    audience_role: Optional[str] = Field(default=None)

    agent_name: str = Field(default="", description="Agent name from the profile.")
    mission: str = Field(default="", description="Mission statement (if not external-facing).")
    personality: dict[str, str] = Field(
        default_factory=dict,
        description="Personality settings: tone, verbosity, formality.",
    )
    active_goals: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Active goals matching this context (filtered by domain if any).",
    )
    standing_instructions: list[str] = Field(
        default_factory=list,
        description=(
            "Instruction texts applicable to this channel/audience_role, "
            "sorted by priority (highest first)."
        ),
    )
    owner_preferences: dict[str, str] = Field(
        default_factory=dict,
        description="Relevant owner preferences as key/value dict.",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="ID of the ProfileContextRequest that triggered this view.",
    )
    frame_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ================================================================ ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="agent_profile",
        schema=AgentProfile,
        description=(
            "The assistant's core identity: name, mission, and personality. "
            "Root profile object — typically one per assistant."
        ),
    ),
    ObjectType(
        name="goal",
        schema=Goal,
        description=(
            "A standing goal the assistant is working toward. "
            "Persistent across sessions; informs prioritization and relevance."
        ),
    ),
    ObjectType(
        name="standing_instruction",
        schema=StandingInstruction,
        description=(
            "A standing instruction scoped by channel and audience_role. "
            "Injected into behavior context when channel/role match."
        ),
    ),
    ObjectType(
        name="personality_profile",
        schema=PersonalityProfile,
        description=(
            "Tone, verbosity, and formality settings, optionally scoped "
            "per channel and audience role."
        ),
    ),
    ObjectType(
        name="owner_preference",
        schema=OwnerPreference,
        description=(
            "A named key/value preference set by the owner. "
            "Persistent; domain and channel scoped."
        ),
    ),
    ObjectType(
        name="profile_context_request",
        schema=ProfileContextRequest,
        description=(
            "Request to assemble a scoped profile context view. "
            "Triggers profile_context_provider behavior."
        ),
    ),
    ObjectType(
        name="profile_context_view",
        schema=ProfileContextView,
        description=(
            "Assembled profile context for a specific channel/audience_role. "
            "Created by profile_context_provider in response to a request."
        ),
    ),
]


# ================================================================ RelationType list

RELATION_TYPES = [
    RelationType(
        name="owns_goal",
        source_types=("agent_profile",),
        target_types=("goal",),
        description="A profile owns a goal.",
    ),
    RelationType(
        name="owns_instruction",
        source_types=("agent_profile",),
        target_types=("standing_instruction",),
        description="A profile owns a standing instruction.",
    ),
    RelationType(
        name="owns_preference",
        source_types=("agent_profile",),
        target_types=("owner_preference",),
        description="A profile owns an owner preference.",
    ),
    RelationType(
        name="fulfilled_by_profile",
        source_types=("profile_context_request",),
        target_types=("profile_context_view",),
        description="A context request is fulfilled by a context view.",
    ),
    RelationType(
        name="triggers_context_for",
        source_types=("auth_context", "frame"),
        target_types=("profile_context_request",),
        description=(
            "An auth_context or frame auto-triggers a profile context request. "
            "Created by profile_context_trigger and frame_context_trigger behaviors."
        ),
    ),
]
