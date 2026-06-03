"""Communication Pack settings."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CommunicationSettings(BaseModel):
    """Settings for the Communication Pack.

    Controls intent detection, thread tracking, and response dispatch.
    """

    intent_detection_mode: str = Field(
        default="heuristic",
        description=(
            "How to detect intent. 'heuristic' uses keyword/pattern rules. "
            "'llm' delegates to an LLM behavior (requires LLM capability). "
            "Default: 'heuristic'."
        ),
    )
    auto_create_threads: bool = Field(
        default=True,
        description=(
            "When True, thread_tracker auto-creates CommThread objects for "
            "incoming messages that have no existing thread. Default: True."
        ),
    )
    default_channel: str = Field(
        default="chat",
        description="Default channel for messages without an explicit channel. Default: 'chat'.",
    )
    low_confidence_intent_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "Intent confidence below this value is flagged as low-confidence "
            "and intent is set to 'unknown'. Default: 0.5."
        ),
    )
    auto_dispatch_approved_responses: bool = Field(
        default=True,
        description=(
            "When True, response_dispatcher fires automatically on "
            "comm_response_candidate.status == approved. Default: True."
        ),
    )
    max_thread_participants: int = Field(
        default=50,
        description="Max number of participants tracked per thread. Default: 50.",
    )
