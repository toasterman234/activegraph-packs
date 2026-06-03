"""Settings for Memory Gateway Pack."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryGatewaySettings(BaseModel):
    """Configuration for Memory Gateway Pack v0.1.

    Controls candidate evaluation, storage limits, and retrieval behavior.
    """

    acceptance_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum confidence score for a memory_candidate to be accepted "
            "and promoted to a MemoryItem. Candidates below this threshold "
            "are rejected with a 'low_confidence' judgment."
        ),
    )

    max_items: int = Field(
        default=1000,
        ge=1,
        description=(
            "Maximum number of MemoryItems to store. When exceeded, the "
            "least-recently-used items are evicted. Set to 0 for unlimited."
        ),
    )

    backend_url: str = Field(
        default=":memory:",
        description=(
            "SQLite database URL for memory storage. Defaults to in-memory "
            "SQLite (no persistence across runs). Use a file path like "
            "'memory.db' for persistence."
        ),
    )

    retrieval_top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of MemoryItems returned per retrieval.",
    )

    min_retrieval_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for a MemoryItem to appear in retrieval results.",
    )

    auto_accept_categories: list[str] = Field(
        default=["preference", "instruction", "decision"],
        description=(
            "Memory categories that are auto-accepted regardless of confidence "
            "if confidence >= acceptance_threshold."
        ),
    )
