"""Research Pack settings — v0.1."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchSettings(BaseModel):
    min_idea_novelty_score: float = Field(
        default=0.4, ge=0.0, le=1.0,
        description="Minimum novelty score for IdeaAtom to be included in direction synthesis.",
    )
    min_coherence_for_hypothesis: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Minimum coherence score for IdeaAtom to trigger hypothesis_generator.",
    )
    max_ideas_per_paper: int = Field(
        default=5, ge=1, le=20,
        description="Maximum IdeaAtom objects extracted per paper.",
    )
    max_claims_per_paper: int = Field(
        default=8, ge=1, le=30,
        description="Maximum claim observations extracted per paper abstract.",
    )
    auto_synthesize_directions: bool = Field(
        default=True,
        description="When True, research_direction_synthesizer fires automatically on new idea atoms.",
    )
    min_ideas_for_direction: int = Field(
        default=2, ge=1,
        description="Minimum number of idea atoms needed to synthesize a research direction.",
    )
