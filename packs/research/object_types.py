"""Research Pack object and relation types — v0.1."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


class Paper(BaseModel):
    title: str = Field(description="Full paper title.")
    abstract: str = Field(default="", description="Paper abstract text.")
    year: Optional[int] = Field(default=None, description="Publication year.")
    doi: Optional[str] = Field(default=None)
    arxiv_id: Optional[str] = Field(default=None)
    venue_id: Optional[str] = Field(default=None, description="ID of the Venue object.")
    author_ids: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    citation_count: int = Field(default=0)
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Author(BaseModel):
    name: str
    email: Optional[str] = Field(default=None)
    affiliation: Optional[str] = Field(default=None)
    semantic_scholar_id: Optional[str] = Field(default=None)
    h_index: Optional[int] = Field(default=None)
    paper_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Venue(BaseModel):
    name: str
    kind: Literal["journal", "conference", "workshop", "preprint", "other"] = Field(default="other")
    abbreviation: Optional[str] = Field(default=None)
    impact_factor: Optional[float] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Method(BaseModel):
    name: str
    description: str = Field(default="")
    paper_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Benchmark(BaseModel):
    name: str
    task: str = Field(default="", description="Task the benchmark evaluates.")
    metric: str = Field(default="", description="Primary metric name (e.g. accuracy, F1).")
    sota_value: Optional[float] = Field(default=None)
    sota_paper_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Dataset(BaseModel):
    name: str
    description: str = Field(default="")
    size: Optional[str] = Field(default=None, description="E.g. '100k examples'.")
    domain: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IdeaAtom(BaseModel):
    """Atomic research idea distilled from one or more papers."""
    text: str = Field(description="One-sentence statement of the idea.")
    source_paper_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    novelty_score: float = Field(default=0.5, ge=0.0, le=1.0)
    coherence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchDirection(BaseModel):
    """A synthesized research direction from multiple idea atoms."""
    title: str
    summary: str = Field(default="")
    idea_atom_ids: list[str] = Field(default_factory=list)
    status: Literal["candidate", "active", "published", "abandoned"] = Field(default="candidate")
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Experiment(BaseModel):
    title: str
    hypothesis: str = Field(default="")
    direction_id: Optional[str] = Field(default=None)
    status: Literal["proposed", "running", "completed", "failed", "abandoned"] = Field(default="proposed")
    result_summary: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


OBJECT_TYPES = [
    ObjectType(name="paper", schema=Paper,
               description="A research paper with title, abstract, authors, venue, and metadata."),
    ObjectType(name="author", schema=Author,
               description="A research author with affiliation and paper list."),
    ObjectType(name="venue", schema=Venue,
               description="A publication venue: journal, conference, workshop, or preprint server."),
    ObjectType(name="method", schema=Method,
               description="A research method or algorithm referenced in one or more papers."),
    ObjectType(name="benchmark", schema=Benchmark,
               description="A benchmark task with metric and state-of-the-art tracking."),
    ObjectType(name="dataset", schema=Dataset,
               description="A research dataset referenced in papers."),
    ObjectType(name="idea_atom", schema=IdeaAtom,
               description="An atomic research idea distilled from papers."),
    ObjectType(name="research_direction", schema=ResearchDirection,
               description="A synthesized research direction from multiple idea atoms."),
    ObjectType(name="experiment", schema=Experiment,
               description="A proposed or running research experiment."),
]

RELATION_TYPES = [
    RelationType(name="cites", source_types=("paper",), target_types=("paper",),
                 description="Paper A cites Paper B."),
    RelationType(name="authored_by", source_types=("paper",), target_types=("author",),
                 description="Paper authored by an Author."),
    RelationType(name="published_in", source_types=("paper",), target_types=("venue",),
                 description="Paper published in a Venue."),
    RelationType(name="uses_method", source_types=("paper",), target_types=("method",),
                 description="Paper uses a Method."),
    RelationType(name="reports_benchmark", source_types=("paper",), target_types=("benchmark",),
                 description="Paper reports results on a Benchmark."),
    RelationType(name="uses_dataset", source_types=("paper",), target_types=("dataset",),
                 description="Paper uses a Dataset."),
    RelationType(name="proposes_idea", source_types=("paper",), target_types=("idea_atom",),
                 description="Paper proposes or implies an IdeaAtom."),
    RelationType(name="composes_direction", source_types=("idea_atom",), target_types=("research_direction",),
                 description="IdeaAtom contributes to a ResearchDirection."),
    RelationType(name="tests_direction", source_types=("experiment",), target_types=("research_direction",),
                 description="Experiment tests a ResearchDirection hypothesis."),
]
