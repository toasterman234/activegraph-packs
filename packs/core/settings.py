"""Settings for the Core Pack.

All fields have defaults — Core works with zero configuration.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CoreSettings(BaseModel):
    """Configuration for Core Pack v0.1.

    Core Pack is deliberately minimal. These settings only control
    the lightweight deterministic behaviors included in v0.1.
    """

    observation_min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum confidence threshold for observations extracted by "
            "observation_extractor. Observations below this threshold are "
            "still created but tagged with low_confidence=True."
        ),
    )

    task_link_similarity_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum word-overlap ratio for task_linker to create a "
            "'produces' relation between an observation and an existing task. "
            "Higher = more conservative linking."
        ),
    )

    max_observations_per_source: int = Field(
        default=10,
        ge=1,
        le=100,
        description=(
            "Maximum number of observations the observation_extractor will "
            "create from a single source object."
        ),
    )

    auto_accept_memory_candidates: bool = Field(
        default=False,
        description=(
            "If True, memory_candidate objects are automatically marked as "
            "accepted=True when created. In production, Memory Gateway Pack "
            "handles acceptance decisions; this is only for standalone demos."
        ),
    )
