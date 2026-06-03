"""Chat Adapter Pack object and relation types — v0.1.

Chat-specific types that complement the channel-neutral Communication Pack.

Design rule: Chat Pack owns the chat-specific UX objects (session, turn, raw input).
It translates ChatInput → CommMessage so Communication Pack behaviors can process it.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ================================================================ Schemas


class ChatInput(BaseModel):
    """Raw input received from a chat interface.

    ChatInput is the entry point for the Chat adapter. chat_ingester fires on
    chat_input.created and translates it into a CommMessage (channel=chat).

    Input shape mirrors the common {"role": "user", "content": "..."} pattern
    used by most LLM APIs, with additional session continuity fields.
    """

    user_ref: str = Field(
        description="Reference to the user sending the message (email, username, ID, etc.)."
    )
    content: str = Field(description="The user's message content.")
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "ID of the ChatSession to continue. If None, chat_ingester creates "
            "a new session and thread."
        ),
    )
    frame_id: Optional[str] = Field(
        default=None,
        description="ID of the frame this input belongs to.",
    )
    role: str = Field(
        default="user",
        description="Message role (always 'user' for inbound input). Reserved for future use.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    """A persistent chat session between a user and the assistant.

    A ChatSession groups multiple ChatTurns into a coherent conversation.
    It links to a CommThread for the channel-neutral view.

    Sessions persist across turns and can be resumed with session_id.
    """

    user_ref: str = Field(
        description="Reference to the user (email, username, ID, etc.)."
    )
    started_at: str = Field(
        default="",
        description="ISO 8601 datetime when the session started.",
    )
    ended_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime when the session ended (None if still active).",
    )
    status: Literal["active", "idle", "closed"] = Field(
        default="active",
        description="Session lifecycle status.",
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="ID of the CommThread associated with this session.",
    )
    turn_count: int = Field(
        default=0,
        description="Number of turns completed in this session.",
    )
    llm_config: dict[str, Any] = Field(
        default_factory=dict,
        description="LLM model configuration used for this session (model name, temperature, etc.).",
    )
    frame_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatTurn(BaseModel):
    """A single request-response turn in a ChatSession.

    A ChatTurn captures the user's message and the assistant's response
    for one exchange. The assistant_message is populated when a
    CommResponseCandidate is delivered.

    Turn numbers are 1-indexed (turn 1 is the first exchange).
    """

    session_id: str = Field(description="ID of the ChatSession this turn belongs to.")
    user_message: str = Field(description="The user's message for this turn.")
    assistant_message: Optional[str] = Field(
        default=None,
        description="The assistant's response (populated after delivery).",
    )
    turn_number: int = Field(
        default=1,
        ge=1,
        description="Turn number within the session (1-indexed).",
    )
    comm_message_id: Optional[str] = Field(
        default=None,
        description="ID of the CommMessage created from this turn's user input.",
    )
    response_candidate_id: Optional[str] = Field(
        default=None,
        description="ID of the CommResponseCandidate for this turn's response.",
    )
    frame_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ================================================================ ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="chat_input",
        schema=ChatInput,
        description=(
            "Raw input from a chat interface. chat_ingester fires on chat_input.created "
            "and translates it into CommMessage(channel=chat)."
        ),
    ),
    ObjectType(
        name="chat_session",
        schema=ChatSession,
        description=(
            "A persistent chat session grouping multiple ChatTurns. "
            "Links to a CommThread for the channel-neutral view."
        ),
    ),
    ObjectType(
        name="chat_turn",
        schema=ChatTurn,
        description=(
            "A single request-response exchange in a ChatSession. "
            "user_message is set on creation; assistant_message is populated after delivery."
        ),
    ),
]


# ================================================================ RelationType list

RELATION_TYPES = [
    RelationType(
        name="session_contains_turn",
        source_types=("chat_session",),
        target_types=("chat_turn",),
        description="A ChatSession contains a ChatTurn.",
    ),
    RelationType(
        name="turn_from_input",
        source_types=("chat_turn",),
        target_types=("chat_input",),
        description="A ChatTurn was created from a ChatInput.",
    ),
    RelationType(
        name="session_has_thread",
        source_types=("chat_session",),
        target_types=("comm_thread",),
        description="A ChatSession corresponds to a CommThread.",
    ),
]
