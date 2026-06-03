"""Email Pack object and relation types — v0.1.

Email-specific types that complement the channel-neutral Communication Pack.

Design rule: Email Pack owns email-specific structure (headers, threading, drafts,
MIME bodies). It translates EmailMessage → CommMessage so Communication Pack
and domain pack behaviors can process emails uniformly.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ================================================================ Schemas


class EmailMessage(BaseModel):
    """A raw inbound email message.

    EmailMessage captures all channel-specific email structure: headers,
    MIME bodies, threading references. email_ingester fires on
    email_message.created and produces:
      - Core Source(kind=email)
      - CommMessage(channel=email)
      - EmailThread (created or updated)

    SMTP/IMAP connection is out of scope — production adapters inject
    EmailMessage objects via tool calls or webhooks.
    """

    message_id: str = Field(
        description=(
            "RFC 2822 Message-ID header value, e.g. '<abc123@mail.example.com>'. "
            "Used for deduplication and threading."
        )
    )
    from_addr: str = Field(description="Sender email address, e.g. 'alice@example.com'.")
    to_addrs: list[str] = Field(
        default_factory=list,
        description="List of To: recipient email addresses.",
    )
    cc_addrs: list[str] = Field(
        default_factory=list,
        description="List of Cc: recipient email addresses.",
    )
    subject: str = Field(default="", description="Email subject line.")
    body_text: str = Field(
        default="",
        description="Plain-text email body (preferred for processing).",
    )
    body_html: Optional[str] = Field(
        default=None,
        description="HTML email body (optional, used for rendering only).",
    )
    thread_id: Optional[str] = Field(
        default=None,
        description=(
            "Thread identifier derived from In-Reply-To / References headers. "
            "If set, email_ingester links this message to the matching EmailThread."
        ),
    )
    in_reply_to: Optional[str] = Field(
        default=None,
        description="RFC 2822 In-Reply-To header value.",
    )
    references: list[str] = Field(
        default_factory=list,
        description="RFC 2822 References header values (list of message IDs).",
    )
    received_at: str = Field(
        default="",
        description="ISO 8601 datetime when this email was received.",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Additional email headers as key-value pairs.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailThread(BaseModel):
    """An email thread grouping related messages by In-Reply-To / References.

    EmailThread is created or updated by email_ingester when a new
    EmailMessage arrives. The thread_id matches the CommThread.thread_id
    for the channel-neutral view.
    """

    thread_id: str = Field(
        description="Canonical thread identifier (from email headers or auto-generated)."
    )
    subject: str = Field(
        default="",
        description="Thread subject (from the first message, stripped of Re:/Fwd: prefixes).",
    )
    participant_addrs: list[str] = Field(
        default_factory=list,
        description="All email addresses that have appeared in this thread.",
    )
    message_count: int = Field(
        default=0,
        description="Running count of messages in this thread.",
    )
    last_message_at: str = Field(
        default="",
        description="ISO 8601 datetime of the most recent message.",
    )
    first_message_id: Optional[str] = Field(
        default=None,
        description="message_id of the first (root) email in this thread.",
    )
    comm_thread_id: Optional[str] = Field(
        default=None,
        description="ID of the CommThread object corresponding to this email thread.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailDraft(BaseModel):
    """A draft outbound email produced by reply_drafter.

    EmailDraft is created when a CommResponseCandidate (channel=email) is ready.
    It formats the response content as a proper email with headers, signature,
    and threading context.

    Approval flow:
      email_draft.created → send_approver checks policy → status updated →
      (if approved) response_dispatcher sends CommResponseCandidate.status = sent
    """

    to_addrs: list[str] = Field(
        default_factory=list,
        description="Recipient email address(es).",
    )
    cc_addrs: list[str] = Field(
        default_factory=list,
        description="Cc: email addresses.",
    )
    subject: str = Field(default="", description="Email subject line.")
    body: str = Field(
        default="",
        description="Email body content (plain text or HTML, per EmailSettings.default_reply_format).",
    )
    in_reply_to_message_id: Optional[str] = Field(
        default=None,
        description="RFC 2822 message_id of the email being replied to.",
    )
    response_candidate_id: Optional[str] = Field(
        default=None,
        description="ID of the CommResponseCandidate this draft fulfills.",
    )
    artifact_id: Optional[str] = Field(
        default=None,
        description="ID of a Core Artifact if the draft was produced from one.",
    )
    status: Literal["draft", "approved", "sent", "rejected"] = Field(
        default="draft",
        description="Draft lifecycle status.",
    )
    requires_approval: bool = Field(
        default=True,
        description="True when send_approver requires owner confirmation before sending.",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Reason if status='rejected'.",
    )
    sent_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime when the draft was sent (populated on send).",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# ================================================================ ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="email_message",
        schema=EmailMessage,
        description=(
            "A raw inbound email. email_ingester fires on email_message.created and "
            "produces Source + CommMessage + EmailThread."
        ),
    ),
    ObjectType(
        name="email_thread",
        schema=EmailThread,
        description=(
            "An email thread grouping related messages by In-Reply-To / References. "
            "Created/updated by email_ingester."
        ),
    ),
    ObjectType(
        name="email_draft",
        schema=EmailDraft,
        description=(
            "A draft outbound email created by reply_drafter. "
            "send_approver gates delivery. Lifecycle: draft → approved/rejected → sent."
        ),
    ),
]


# ================================================================ RelationType list

RELATION_TYPES = [
    RelationType(
        name="email_thread_contains",
        source_types=("email_thread",),
        target_types=("email_message",),
        description="An EmailThread contains an EmailMessage.",
    ),
    RelationType(
        name="draft_responds_to",
        source_types=("email_draft",),
        target_types=("email_message",),
        description="An EmailDraft is a response to an EmailMessage.",
    ),
    RelationType(
        name="draft_from_candidate",
        source_types=("email_draft",),
        target_types=("comm_response_candidate",),
        description="An EmailDraft was produced from a CommResponseCandidate.",
    ),
    RelationType(
        name="email_linked_to_comm_thread",
        source_types=("email_thread",),
        target_types=("comm_thread",),
        description="An EmailThread corresponds to a CommThread.",
    ),
]
