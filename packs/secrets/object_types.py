"""Secrets Pack object and relation types — v0.1.

Manages credential references, scopes, and usage tracking.

CRITICAL INVARIANT: Actual secret values NEVER appear in:
- Graph objects
- Events
- Behaviors
- Artifacts
- Logs

CredentialRef contains a NAME only. The actual secret is resolved
at execution time from environment variables (or a vault backend in v0.2).

This pack exists to make credential usage auditable without exposing secrets.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ================================================================ Schemas


class CredentialRef(BaseModel):
    """A reference to a credential — never stores the actual secret.

    The actual secret is looked up at runtime from:
    1. Environment variable: ${env_prefix}${name.upper()}
    2. Future: vault backend (v0.2)

    Examples:
    - name="OPENAI_API_KEY" → reads env var OPENAI_API_KEY
    - name="STRIPE_SK" → reads env var STRIPE_SK

    CredentialRef objects are safe to include in graph state because
    they contain no secret data.
    """

    name: str = Field(
        description=(
            "Name of the credential. Also used as the environment variable "
            "name (after applying env_prefix from SecretsSettings)."
        )
    )
    scope: str = Field(
        default="",
        description=(
            "Scope or permission level of this credential. "
            "Examples: 'read', 'write', 'admin', 'send_email', 'read_crm'."
        ),
    )
    provider_hint: Optional[str] = Field(
        default=None,
        description=(
            "Name of the capability provider that uses this credential. "
            "Examples: 'openai', 'stripe', 'gmail', 'github'."
        ),
    )
    last_used_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime of the last time this credential was resolved.",
    )
    use_count: int = Field(
        default=0,
        ge=0,
        description="Number of times this credential has been resolved.",
    )
    enabled: bool = Field(
        default=True,
        description="If False, all resolution attempts are rejected.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class SecretUsageEvent(BaseModel):
    """Records that a credential was resolved and used.

    Created every time Secrets Pack resolves a CredentialRef.
    This provides a complete audit trail of credential usage
    without ever recording the actual secret value.
    """

    credential_ref_name: str = Field(
        description="Name of the credential that was resolved.",
    )
    behavior_name: Optional[str] = Field(
        default=None,
        description="Name of the behavior or tool that requested resolution.",
    )
    resolved: bool = Field(
        default=True,
        description="True if the credential was found and resolved successfully.",
    )
    frame_id: Optional[str] = Field(default=None)
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime of resolution.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# ================================================================ ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="credential_ref",
        schema=CredentialRef,
        description=(
            "A reference to a credential — contains the credential NAME only, "
            "never the actual secret. Safe to include in graph state and logs."
        ),
    ),
    ObjectType(
        name="secret_usage_event",
        schema=SecretUsageEvent,
        description=(
            "Records that a credential was resolved and used. "
            "Provides audit trail without exposing actual secret values."
        ),
    ),
]


# ================================================================ RelationType list

RELATION_TYPES = [
    RelationType(
        name="credential_used_in",
        source_types=("secret_usage_event",),
        target_types=("capability_call",),
        description="A secret usage event is associated with a capability call.",
    ),
]
