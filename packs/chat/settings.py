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
            "When True, chat_memory_context retrieves relevant long-term memories "
            "and folds them into the LLM context (requires Memory Gateway Pack). "
            "Set False to disable cross-session recall. Default: True."
        ),
    )
    memory_write_path: str = Field(
        default="heuristic",
        description=(
            "How chat turns become durable memory candidates. 'heuristic' runs the "
            "built-in zero-LLM chat_memory_proposer (the default automatic write "
            "path). 'off' disables it so an external ingestion pack — LLM extraction, "
            "entity extraction, mem0, etc. — owns the write path instead. The swap "
            "seam is the memory_candidate object: any pack that emits memory_candidate "
            "objects feeds the same lifecycle without editing the Chat Pack. "
            "Default: 'heuristic'."
        ),
    )
    memory_backend_url: str = Field(
        default=":memory:",
        description=(
            "Backend URL chat_memory_context queries for recall. MUST match "
            "MemoryGatewaySettings.backend_url so retrieval reads what memory_writer "
            "stored. Defaults to ':memory:' (matches the Memory Gateway default for "
            "zero-config use); set both to a file path for cross-session persistence."
        ),
    )
    memory_top_k: int = Field(
        default=3,
        description=(
            "Maximum number of long-term memories chat_memory_context folds into "
            "the prompt. Keeps the injected context bounded. Default: 3."
        ),
    )
    memory_min_score: float = Field(
        default=0.1,
        description=(
            "Minimum similarity score (lexical Jaccard or cosine) for a memory to "
            "be recalled. Lower = more recall, higher = more precision. Default: 0.1."
        ),
    )
    memory_subject_scoped: bool = Field(
        default=True,
        description=(
            "When True (default), chat_memory_context only recalls memories whose "
            "subject_ref matches the message sender. This is an access-control "
            "boundary: it prevents one user from receiving another user's stored "
            "memories in a multi-user deployment. Set False ONLY to opt into "
            "shared/global recall where every user sees every memory (e.g. a "
            "single-user assistant)."
        ),
    )
    memory_include_global: bool = Field(
        default=False,
        description=(
            "When subject-scoped recall is on, controls whether subject-less "
            "(NULL) 'global' memories are ALSO recalled alongside the sender's "
            "own. Default False = strict per-user isolation: only the sender's "
            "own memories are returned, so untagged or legacy NULL rows can never "
            "leak across users. Set True to also surface shared/global facts to "
            "every user. Ignored when memory_subject_scoped is False."
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
