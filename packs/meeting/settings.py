"""Meeting Pack settings — v0.1."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MeetingSettings(BaseModel):
    auto_create_tasks_from_action_items: bool = Field(
        default=True,
        description="When True, action_item_extractor creates Core Task objects from meeting action items.",
    )
    decision_keywords: list[str] = Field(
        default_factory=lambda: [
            "decided", "we agreed", "agreed to", "we will", "action item",
            "going forward", "resolved", "confirmed", "approved", "we're going",
            "let's", "let us", "we decided", "consensus", "unanimous",
        ],
        description="Keywords that indicate a transcript segment contains a decision.",
    )
    action_item_keywords: list[str] = Field(
        default_factory=lambda: [
            "will", "action item", "follow up", "to do", "todo", "needs to",
            "should", "by next", "owner:", "due:", "take care of",
            "responsible for", "assigned to", "going to", "i'll", "you'll",
            "we'll", "they'll",
        ],
        description="Keywords that indicate a segment contains an action item.",
    )
    min_segment_words: int = Field(
        default=5,
        description="Minimum word count for a transcript segment to be processed.",
    )
    auto_summarize_meeting: bool = Field(
        default=True,
        description="When True, meeting_summarizer fires automatically after transcript ingestion.",
    )
    max_segments_per_meeting: int = Field(
        default=500,
        description="Maximum TranscriptSegment objects per meeting.",
    )
