"""Identity/Auth Pack object and relation types — v0.1.

Answers: "who is speaking, how confident are we, what can they do?"

Object types:
  principal    — A recognized identity with a role and confidence level
  auth_context — Session-scoped authentication state for a principal
  role         — Named role with a capability list
  permission   — Explicit action/resource grant tied to a role
  delegation   — Temporary scope transfer from one principal to another

Design rules:
  - Principal never stores passwords, tokens, or raw secrets
  - auth_confidence is the system's confidence in the identity claim, not
    the strength of the authentication mechanism
  - Roles and permissions are additive — higher roles accumulate capabilities
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


# ================================================================ Role enum

RoleType = Literal[
    "owner",         # The assistant's owner/operator — highest trust
    "admin",         # Delegated admin — can manage settings and collaborators
    "collaborator",  # Invited team member
    "external",      # Known outside party (investor, partner, vendor)
    "customer",      # Customer / end user
    "unknown",       # Seen before but not verified
    "blocked",       # Explicitly blocked — all permissions denied
]


# ================================================================ Schemas


class Principal(BaseModel):
    """A recognized identity with an assigned role and confidence score.

    Principals are resolved from incoming messages and actions. The same
    person may appear via multiple channels (email, Slack, chat), each
    creating a Principal. Entity Pack handles deduplication and merging.

    Helper methods:
        is_owner()    → role == "owner"
        is_external() → role in (external, customer, unknown)
        can(action)   → True if action is in role's implied capabilities
    """

    name: str = Field(description="Display name (from message header, contact, etc.).")
    role: RoleType = Field(
        default="unknown",
        description="Assigned trust role. Owner = highest trust, blocked = no trust.",
    )
    auth_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "System confidence in this identity claim (0=none, 1=verified). "
            "Not authentication strength — reflects how sure we are who this is."
        ),
    )
    identifiers: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Known identifiers for this principal: "
            "{'email': 'alice@example.com', 'slack_id': 'U123', 'phone': '+1555...'}. "
            "Never contains passwords or tokens."
        ),
    )
    channel: Optional[str] = Field(
        default=None,
        description="Channel this principal was resolved from (chat, email, sms, api).",
    )
    entity_id: Optional[str] = Field(
        default=None,
        description="ID of the Entity graph object for this principal (set by Entity Pack).",
    )
    last_seen_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp of the most recent interaction.",
    )
    seen_count: int = Field(
        default=1,
        ge=1,
        description="Number of times this principal has been seen (incremented on revisit).",
    )
    frame_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_owner(self) -> bool:
        return self.role == "owner"

    def is_external(self) -> bool:
        return self.role in ("external", "customer", "unknown")

    def can(self, action: str) -> bool:
        """Check if this principal's role allows the given action.

        Role capability hierarchy (additive):
            owner       → all actions
            admin       → manage_settings, manage_collaborators, read, write, execute
            collaborator → read, write, comment
            external    → read_public
            customer    → read_own
            unknown     → none
            blocked     → none
        """
        ROLE_CAPABILITIES: dict[str, set[str]] = {
            "owner": {"*"},
            "admin": {"manage_settings", "manage_collaborators", "read", "write", "execute", "comment"},
            "collaborator": {"read", "write", "comment"},
            "external": {"read_public"},
            "customer": {"read_own"},
            "unknown": set(),
            "blocked": set(),
        }
        caps = ROLE_CAPABILITIES.get(self.role, set())
        return "*" in caps or action in caps


class AuthContext(BaseModel):
    """Session-scoped authentication state for a principal.

    Created by auth_context_builder when a principal is resolved.
    Scopes all actions within a frame to a known principal.
    """

    principal_id: str = Field(description="ID of the Principal graph object.")
    principal_role: RoleType = Field(description="Role snapshot at time of context creation.")
    channel: str = Field(
        default="unknown",
        description="Channel this auth context is for (chat, email, api, etc.).",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Opaque session identifier from the channel (never a secret).",
    )
    verified_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp when identity was verified.",
    )
    frame_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Role(BaseModel):
    """Named role with an explicit capability list.

    Roles are additive — higher roles expand capabilities.
    The default role hierarchy is encoded in Principal.can(), but custom
    Role objects can override it for tenant-specific needs.
    """

    name: RoleType = Field(description="Role name (must be one of the RoleType literals).")
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of allowed action strings (e.g. 'read', 'write', 'execute').",
    )
    description: str = Field(default="", description="Human-readable description of the role.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Permission(BaseModel):
    """Explicit action/resource grant scoped to a role.

    Permissions are additive grants — they do not override role defaults.
    Use Delegation for temporary scope changes.
    """

    action: str = Field(description="Action string being granted (e.g. 'read', 'send_email').")
    resource: str = Field(
        default="*",
        description="Resource pattern (e.g. '*', 'email:*', 'artifact:report').",
    )
    granted_to_role: RoleType = Field(description="Role this permission is granted to.")
    granted_by_principal_id: Optional[str] = Field(
        default=None,
        description="Principal who granted this permission.",
    )
    expires_at: Optional[str] = Field(default=None, description="ISO 8601 expiry datetime.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Delegation(BaseModel):
    """Temporary scope transfer from one principal to another.

    Used when an owner temporarily delegates a specific capability
    to a collaborator or external party (e.g., 'allow Bob to approve
    invoices until Friday').
    """

    from_principal_id: str = Field(description="ID of the principal delegating authority.")
    to_principal_id: str = Field(description="ID of the principal receiving authority.")
    scope: str = Field(
        description=(
            "What is being delegated: a capability string, resource pattern, "
            "or free-text scope description."
        ),
    )
    expires_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime when this delegation expires.",
    )
    rationale: str = Field(default="", description="Why this delegation was created.")
    revoked: bool = Field(default=False, description="True if this delegation has been revoked.")
    frame_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ================================================================ ObjectType list

OBJECT_TYPES = [
    ObjectType(
        name="principal",
        schema=Principal,
        description=(
            "A recognized identity with an assigned role and confidence score. "
            "Resolved from incoming messages. Owner = highest trust, blocked = no trust."
        ),
    ),
    ObjectType(
        name="auth_context",
        schema=AuthContext,
        description=(
            "Session-scoped authentication state for a principal. "
            "Scopes all actions within a frame to a known principal."
        ),
    ),
    ObjectType(
        name="role",
        schema=Role,
        description=(
            "Named role with an explicit capability list. "
            "Default hierarchy: owner > admin > collaborator > external > customer > unknown > blocked."
        ),
    ),
    ObjectType(
        name="permission",
        schema=Permission,
        description=(
            "Explicit action/resource grant scoped to a role. "
            "Additive — does not override role defaults."
        ),
    ),
    ObjectType(
        name="delegation",
        schema=Delegation,
        description=(
            "Temporary scope transfer from one principal to another. "
            "Used for time-boxed capability grants."
        ),
    ),
]


# ================================================================ RelationType list

RELATION_TYPES = [
    RelationType(
        name="resolves_to",
        source_types=("source", "comm_message"),
        target_types=("principal",),
        description="A source or comm_message resolves to a principal.",
    ),
    RelationType(
        name="authenticated_by",
        source_types=("principal",),
        target_types=("auth_context",),
        description="A principal is authenticated by an auth context.",
    ),
    RelationType(
        name="granted_by",
        source_types=("delegation",),
        target_types=("principal",),
        description="A delegation is granted by a principal.",
    ),
    RelationType(
        name="granted_to",
        source_types=("delegation",),
        target_types=("principal",),
        description="A delegation is granted to a principal.",
    ),
    RelationType(
        name="linked_to_entity",
        source_types=("principal",),
        target_types=("entity",),
        description="A principal is linked to an Entity pack entity.",
    ),
]
