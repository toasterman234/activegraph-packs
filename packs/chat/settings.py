"""Chat Adapter Pack settings."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatSettings(BaseModel):
    """Settings for the Chat Adapter Pack.

    Controls LLM integration, context assembly, and chat UX behaviors.
    """

    llm_provider: str = Field(
        default="mock",
        description=(
            "LLM provider for chat_llm_responder. 'mock' returns deterministic "
            "stub responses (useful for fixtures/tests). "
            "Other values: 'openai', 'anthropic'. Default: 'mock'."
        ),
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model name. Ignored when llm_provider='mock'. Default: 'gpt-4o-mini'.",
    )
    system_prompt_override: Optional[str] = Field(
        default=None,
        description=(
            "If set, replaces the AgentProfile-assembled system prompt with this literal string. "
            "Useful for testing. Default: None (use AgentProfile context)."
        ),
    )
    max_context_messages: int = Field(
        default=10,
        description=(
            "Maximum number of prior ChatTurn messages to include in the LLM context. "
            "Default: 10."
        ),
    )
    include_memory: bool = Field(
        default=True,
        description=(
            "When True, chat_llm_responder includes relevant memory candidates in context "
            "(requires Memory Gateway Pack). Default: True."
        ),
    )
    include_profile: bool = Field(
        default=True,
        description=(
            "When True, chat_llm_responder includes ProfileContextView in context "
            "(requires Agent Profile Pack). Default: True."
        ),
    )
    auto_approve_responses: bool = Field(
        default=True,
        description=(
            "When True, CommResponseCandidate is automatically approved for chat "
            "without requiring explicit owner approval. Default: True."
        ),
    )
    typing_indicator_enabled: bool = Field(
        default=False,
        description="Reserved for future streaming/WebSocket UX. Default: False.",
    )
