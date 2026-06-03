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

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ================================================================ Schemas


class SecretScope(BaseModel):
    """Defines a permission scope for credentials.

    A scope declares WHAT a credential is allowed to do.
    CredentialRef objects reference a scope by name.

    Examples:
    - scope 'openai:read' — allowed to call OpenAI read-only endpoints
    - scope 'stripe:write' — allowed to create Stripe charges
    - scope 'gmail:send_email' — allowed to send email via Gmail API
    """

    scope_name: str = Field(
        description=(
            "Unique scope identifier. Convention: '{provider}:{operation}' "
            "or '{provider}:{level}'. Examples: 'openai:write', 'stripe:read_only'."
        )
    )
    description: str = Field(
        default="",
        description="Human-readable description of what this scope permits.",
    )
    allowed_providers: list[str] = Field(
        default_factory=list,
        description="Capability provider names this scope applies to.",
    )
    allowed_operations: list[str] = Field(
        default_factory=list,
        description=(
            "Specific operations/capabilities permitted under this scope. "
            "Empty list means all operations for the allowed_providers are permitted."
        ),
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


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
            "Examples: 'read', 'write', 'admin', 'send_email', 'read_crm'. "
            "Should match a SecretScope.scope_name if defined."
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
    """Records that a credential was registered or resolved.

    Created when:
    - A CredentialRef is registered (resolved=False, event_type='registered')
    - A CredentialRef is resolved at call time (resolved=True, event_type='resolved')

    This provides a complete audit trail of credential usage
    without ever recording the actual secret value.
    """

    credential_ref_name: str = Field(
        description="Name of the credential that was registered or resolved.",
    )
    behavior_name: Optional[str] = Field(
        default=None,
        description="Name of the behavior or tool that requested registration/resolution.",
    )
    resolved: bool = Field(
        default=False,
        description="True if the credential was resolved (not just registered).",
    )
    frame_id: Optional[str] = Field(default=None)
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime of the event.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class CredentialRotationEvent(BaseModel):
    """Records that a credential was rotated (replaced with a new secret).

    Created whenever a credential rotation is performed so there is an
    auditable trail of when secrets change. Does NOT store old or new values.
    """

    credential_ref_name: str = Field(
        description="Name of the credential that was rotated.",
    )
    rotated_by: Optional[str] = Field(
        default=None,
        description="Name of the agent, behavior, or user that performed the rotation.",
    )
    reason: str = Field(
        default="",
        description="Reason for the rotation (e.g. 'scheduled', 'suspected_leak', 'expired').",
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime of rotation.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# ================================================================ ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="secret_scope",
        schema=SecretScope,
        description=(
            "Defines a permission scope for credentials — what a credential is "
            "allowed to do. References capability providers and allowed operations."
        ),
    ),
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
            "Records that a credential was registered or resolved. "
            "Provides audit trail without exposing actual secret values."
        ),
    ),
    ObjectType(
        name="credential_rotation_event",
        schema=CredentialRotationEvent,
        description=(
            "Records that a credential was rotated (replaced). "
            "Provides rotation audit trail without storing old/new values."
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
    RelationType(
        name="governed_by",
        source_types=("credential_ref",),
        target_types=("secret_scope",),
        description="A credential reference is governed by a secret scope.",
    ),
]
