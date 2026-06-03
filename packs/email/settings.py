"""Email Pack settings."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EmailSettings(BaseModel):
    """Settings for the Email Pack.

    Controls email ingestion, draft formatting, and approval gates.
    """

    require_approval_for_external: bool = Field(
        default=True,
        description=(
            "When True, outbound emails to external (non-owner) addresses require "
            "owner approval before sending. This is the primary safety gate for "
            "external email writes. Default: True."
        ),
    )
    auto_create_threads: bool = Field(
        default=True,
        description=(
            "When True, email_ingester auto-creates EmailThread objects for emails "
            "that don't reference an existing thread. Default: True."
        ),
    )
    trusted_domains: list[str] = Field(
        default_factory=list,
        description=(
            "List of email domains that are treated as internal/trusted, "
            "which may bypass the external approval gate. Example: ['mycompany.com']. "
            "Default: [] (all external domains require approval)."
        ),
    )
    draft_signature: str = Field(
        default="",
        description=(
            "Optional email signature appended to all outbound drafts. "
            "Supports plain text. Default: '' (no signature)."
        ),
    )
    max_body_length: int = Field(
        default=50_000,
        description=(
            "Maximum email body length (characters) to ingest. "
            "Bodies exceeding this are truncated. Default: 50000."
        ),
    )
    default_reply_format: str = Field(
        default="plain_text",
        description=(
            "Default format for drafted replies: 'plain_text' or 'html'. "
            "Default: 'plain_text'."
        ),
    )
    owner_email_addresses: list[str] = Field(
        default_factory=list,
        description=(
            "Email addresses belonging to the assistant owner. "
            "Used to determine 'is_internal' in send_approver. "
            "Example: ['alice@example.com']."
        ),
    )
