"""Memory Gateway Pack object and relation types — v0.1.

Manages the full memory lifecycle:
  memory_candidate (from Core) → evaluation → MemoryItem (stored)
  retrieval request → MemoryRetrieval → MemoryRanking

Design rule: Core Pack only produces memory_candidates. This pack
decides what to keep, stores accepted items, and handles retrieval.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ================================================================ Schemas


class MemoryItem(BaseModel):
    """A durable memory item — an accepted memory_candidate.

    Created by memory_writer after candidate_evaluator accepts a
    memory_candidate. Stored in the backend (SQLite by default).

    MemoryItems are the long-term memory substrate. They are retrieved
    by behaviors to provide context across frames/sessions.
    """

    text: str = Field(
        description="The memory text — what is remembered, as a statement."
    )
    category: Optional[str] = Field(
        default=None,
        description=(
            "Memory category. Examples: preference, instruction, decision, "
            "fact, relationship, style, context."
        ),
    )
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence score inherited from the accepted memory_candidate.",
    )
    source_ids: list[str] = Field(
        default_factory=list,
        description="IDs of Core source objects that grounded this memory.",
    )
    candidate_id: Optional[str] = Field(
        default=None,
        description="ID of the memory_candidate this item was promoted from.",
    )
    created_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime when this item was created.",
    )
    last_retrieved_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime of the most recent retrieval.",
    )
    retrieval_count: int = Field(
        default=0,
        ge=0,
        description="Number of times this item has been retrieved.",
    )
    subject_ref: Optional[str] = Field(
        default=None,
        description="Opaque reference to who/what this memory is about.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryRetrieval(BaseModel):
    """Records a memory retrieval request and its results.

    Created when a behavior requests memories relevant to a query.
    Links to the MemoryRanking objects that score each result.
    """

    query: str = Field(
        description="The retrieval query (natural language or keyword).",
    )
    behavior_name: Optional[str] = Field(
        default=None,
        description="Name of the behavior that requested this retrieval.",
    )
    frame_id: Optional[str] = Field(
        default=None,
        description="Frame scope for this retrieval.",
    )
    results_count: int = Field(
        default=0,
        ge=0,
        description="Number of items returned.",
    )
    item_ids: list[str] = Field(
        default_factory=list,
        description="IDs of MemoryItem objects returned, in ranked order.",
    )
    retrieved_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime of retrieval.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryRanking(BaseModel):
    """Scores a MemoryItem's relevance for a specific retrieval.

    Created by memory_ranker for each item returned in a retrieval.
    Provides a score and human-readable reason for why this item
    is relevant to the retrieval query.
    """

    retrieval_id: str = Field(
        description="ID of the MemoryRetrieval this ranking belongs to.",
    )
    item_id: str = Field(
        description="ID of the MemoryItem being ranked.",
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance score for this item in this retrieval (0.0–1.0).",
    )
    reason: str = Field(
        default="",
        description="Human-readable explanation of why this item is relevant.",
    )
    rank: int = Field(
        default=1,
        ge=1,
        description="Rank position (1 = most relevant).",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# ================================================================ ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="memory_item",
        schema=MemoryItem,
        description=(
            "A durable memory item — an accepted and stored memory_candidate. "
            "Retrieved by behaviors to provide context across frames/sessions."
        ),
    ),
    ObjectType(
        name="memory_retrieval",
        schema=MemoryRetrieval,
        description=(
            "Records a memory retrieval request and results. "
            "Provides audit trail of what context was fetched and when."
        ),
    ),
    ObjectType(
        name="memory_ranking",
        schema=MemoryRanking,
        description=(
            "Scores a MemoryItem's relevance for a specific retrieval. "
            "Created by memory_ranker for each result."
        ),
    ),
]


# ================================================================ RelationType list

RELATION_TYPES = [
    RelationType(
        name="accepted_as",
        source_types=("memory_candidate",),
        target_types=("memory_item",),
        description="An accepted memory_candidate is promoted to a MemoryItem.",
    ),
    RelationType(
        name="ranked_in",
        source_types=("memory_item",),
        target_types=("memory_retrieval",),
        description="A MemoryItem appears in a retrieval result set.",
    ),
    RelationType(
        name="scored_by",
        source_types=("memory_ranking",),
        target_types=("memory_retrieval",),
        description="A MemoryRanking scores a MemoryItem in a retrieval.",
    ),
]
