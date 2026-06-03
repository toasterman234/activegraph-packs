"""Settings for Identity/Auth Pack."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IdentitySettings(BaseModel):
    """Configuration for Identity/Auth Pack v0.1.

    Controls how principals are resolved, what role is assigned by default,
    and how confidently the system recognizes the owner.
    """

    owner_identifiers: list[str] = Field(
        default_factory=list,
        description=(
            "List of identifier strings that unambiguously identify the owner. "
            "Matched against sender_ref (case-insensitive). "
            "E.g. ['alice@example.com', '+15551234567', 'alice_slack_id']. "
            "A source whose sender_ref matches any of these gets role='owner'."
        ),
    )

    default_external_role: Literal[
        "external", "customer", "unknown"
    ] = Field(
        default="unknown",
        description=(
            "Default role assigned to principals that don't match any owner "
            "identifier and aren't in a known collaborator list. "
            "Use 'external' for known-but-untrusted parties, 'unknown' for "
            "completely new contacts."
        ),
    )

    owner_auth_confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description=(
            "Auth confidence assigned to owner-matched principals. "
            "High but not 1.0 — full certainty requires cryptographic proof."
        ),
    )

    default_auth_confidence: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description=(
            "Auth confidence assigned to non-owner principals without "
            "additional verification signals."
        ),
    )

    create_auth_context: bool = Field(
        default=True,
        description=(
            "If True, auth_context_builder creates an AuthContext whenever "
            "a principal is resolved. Set False to disable session tracking."
        ),
    )

    check_permissions_on_proposed_actions: bool = Field(
        default=True,
        description=(
            "If True, permission_checker fires on action.created with "
            "status=proposed and validates the principal's role. "
            "Rejected actions are patched to status='rejected'."
        ),
    )

    auto_deduplicate_principals: bool = Field(
        default=True,
        description=(
            "If True, principal_resolver checks the local registry for an "
            "existing principal with the same normalized sender_ref. On match, "
            "patches last_seen_at and increments seen_count rather than "
            "creating a new Principal. Set False to disable dedup (testing)."
        ),
    )
