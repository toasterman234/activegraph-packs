"""Meeting Pack object and relation types — v0.1."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


class Meeting(BaseModel):
    title: str
    date: Optional[str] = Field(default=None, description="ISO 8601 date string.")
    duration_minutes: Optional[int] = Field(default=None)
    platform: Literal["zoom", "teams", "google_meet", "in_person", "phone", "other"] = Field(default="other")
    participants: list[str] = Field(default_factory=list, description="Participant refs (emails or names).")
    recording_url: Optional[str] = Field(default=None)
    source_id: Optional[str] = Field(default=None)
    status: Literal["scheduled", "completed", "cancelled"] = Field(default="completed")
    metadata: dict[str, Any] = Field(default_factory=dict)


class TranscriptSegment(BaseModel):
    meeting_id: str
    speaker: str = Field(description="Speaker name or ref.")
    text: str = Field(description="Transcript text for this segment.")
    timestamp_seconds: Optional[float] = Field(default=None)
    segment_index: int = Field(default=0)
    is_decision: bool = Field(default=False, description="Flagged as containing a decision.")
    is_action_item: bool = Field(default=False, description="Flagged as containing an action item.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class MeetingDecision(BaseModel):
    meeting_id: str
    text: str = Field(description="The decision as a statement.")
    segment_id: Optional[str] = Field(default=None)
    decided_by: list[str] = Field(default_factory=list, description="Participant refs who made/confirmed the decision.")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MeetingActionItem(BaseModel):
    meeting_id: str
    text: str = Field(description="Action item description.")
    owner_ref: Optional[str] = Field(default=None, description="Who owns this action item.")
    due_at: Optional[str] = Field(default=None)
    segment_id: Optional[str] = Field(default=None)
    task_id: Optional[str] = Field(default=None, description="Link to Core Task created from this action item.")
    status: Literal["open", "done", "cancelled"] = Field(default="open")
    metadata: dict[str, Any] = Field(default_factory=dict)


class MeetingNote(BaseModel):
    meeting_id: str
    content: str = Field(description="Meeting summary or notes in markdown.")
    note_type: Literal["summary", "minutes", "highlights", "raw"] = Field(default="summary")
    artifact_id: Optional[str] = Field(default=None, description="Link to Core Artifact.")
    metadata: dict[str, Any] = Field(default_factory=dict)


OBJECT_TYPES = [
    ObjectType(name="meeting", schema=Meeting,
               description="A meeting with participants, platform, and transcript source."),
    ObjectType(name="transcript_segment", schema=TranscriptSegment,
               description="A segment of a meeting transcript (one speaker turn)."),
    ObjectType(name="meeting_decision", schema=MeetingDecision,
               description="A decision made during a meeting."),
    ObjectType(name="meeting_action_item", schema=MeetingActionItem,
               description="An action item identified in a meeting (linked to Core task)."),
    ObjectType(name="meeting_note", schema=MeetingNote,
               description="A note or summary of a meeting."),
]

RELATION_TYPES = [
    RelationType(name="segment_of", source_types=("transcript_segment",), target_types=("meeting",),
                 description="TranscriptSegment belongs to a Meeting."),
    RelationType(name="decision_in", source_types=("meeting_decision",), target_types=("meeting",),
                 description="Decision made in a Meeting."),
    RelationType(name="action_item_in", source_types=("meeting_action_item",), target_types=("meeting",),
                 description="ActionItem identified in a Meeting."),
    RelationType(name="note_for", source_types=("meeting_note",), target_types=("meeting",),
                 description="Note written for a Meeting."),
    RelationType(name="decision_from_segment", source_types=("meeting_decision",),
                 target_types=("transcript_segment",),
                 description="Decision extracted from a specific segment."),
    RelationType(name="action_item_from_segment", source_types=("meeting_action_item",),
                 target_types=("transcript_segment",),
                 description="Action item extracted from a specific segment."),
    RelationType(name="action_creates_task", source_types=("meeting_action_item",), target_types=("task",),
                 description="Meeting action item promoted to a Core task."),
    RelationType(name="derived_from_source", source_types=("meeting",), target_types=("source",),
                 description="Meeting derived from a transcript source."),
]
