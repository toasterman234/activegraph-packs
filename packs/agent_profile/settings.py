"""Settings for Agent Profile Pack."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentProfileSettings(BaseModel):
    """Configuration for Agent Profile Pack v0.1.

    Sensible defaults so the pack works without any configuration.
    Override to customize the assistant's identity and style.
    """

    default_agent_name: str = Field(
        default="Assistant",
        description="Default name for the assistant if no AgentProfile object is created.",
    )

    default_mission: str = Field(
        default="Help the owner accomplish their goals efficiently.",
        description="Default mission statement used when no AgentProfile is loaded.",
    )

    default_tone: Literal["neutral", "warm", "direct", "formal", "casual", "technical"] = Field(
        default="neutral",
        description="Default communication tone.",
    )

    default_verbosity: Literal["concise", "balanced", "detailed"] = Field(
        default="balanced",
        description="Default verbosity level.",
    )

    default_formality: Literal["informal", "neutral", "formal"] = Field(
        default="neutral",
        description="Default formality level.",
    )

    owner_name: Optional[str] = Field(
        default=None,
        description=(
            "Name of the owner this assistant serves. "
            "Used in context views and standing instructions."
        ),
    )

    expose_mission_to_external: bool = Field(
        default=False,
        description=(
            "If True, the mission statement is included in external-facing "
            "context views. If False (default), mission is owner-only."
        ),
    )

    max_standing_instructions: int = Field(
        default=20,
        ge=1,
        description=(
            "Maximum number of standing instructions to include in a "
            "context view. Sorted by priority (highest first)."
        ),
    )

    max_active_goals: int = Field(
        default=10,
        ge=1,
        description=(
            "Maximum number of active goals to include in a context view. "
            "Sorted by priority (critical > high > medium > low)."
        ),
    )
