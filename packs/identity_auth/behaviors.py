"""Identity/Auth Pack behaviors — v0.1.

Three behaviors covering the full identity lifecycle:

1. principal_resolver — on source.created, extracts sender_ref and resolves
   it to a Principal. Assigns role 'owner' if sender_ref matches any
   owner_identifier in settings; otherwise assigns default_external_role.

2. auth_context_builder — on principal.created, creates an AuthContext
   that scopes the session for downstream behaviors.

3. permission_checker — on action.created (status=proposed), validates
   that the proposing principal's role allows the action. Rejects
   actions from blocked principals or those lacking required capabilities.

Design rules:
- Behaviors must NOT call graph.objects() — only add_object, add_relation,
  get_object, patch_object are safe in behavior context
- Principals never store passwords, tokens, or actual secrets
- Permission checks use role hierarchy (Principal.can(action))
- principal_id must be in action.metadata for permission_checker to fire
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from activegraph.packs import behavior

from .object_types import AuthContext, Principal
from .settings import IdentitySettings


# ------------------------------------------------------------------ helpers

def _normalize_identifier(s: str) -> str:
    return s.strip().lower()


def _matches_owner_identifiers(sender_ref: str, owner_identifiers: list[str]) -> bool:
    """Check if sender_ref matches any owner identifier (case-insensitive)."""
    norm = _normalize_identifier(sender_ref)
    return any(_normalize_identifier(oid) == norm for oid in owner_identifiers)


# ------------------------------------------------------------------ behaviors


@behavior(
    name="principal_resolver",
    on=["object.created"],
    where={"object.type": "source"},
    creates=["principal"],
)
def principal_resolver(event, graph, ctx, *, settings: IdentitySettings):
    """Resolve a source's sender_ref to a Principal.

    On: object.created (source)
    Creates: principal with assigned role and auth_confidence
    Creates: resolves_to(source → principal) relation

    If sender_ref matches any owner_identifier from settings, assigns
    role='owner' with owner_auth_confidence. Otherwise assigns
    default_external_role with default_auth_confidence.

    In v0.1 this always creates a new Principal (dedup is v0.2 via Entity Pack).
    The caller should check existing principals before calling resolve if dedup
    is important — the fixture tests use explicit IDs to avoid duplicates.
    """
    obj = event.payload.get("object", {})
    source_id = obj.get("id")
    source_data = obj.get("data", {})

    sender_ref = source_data.get("sender_ref", "")
    channel = source_data.get("channel", "unknown")
    frame_id = source_data.get("frame_id")

    if not sender_ref:
        return

    now = datetime.now(timezone.utc).isoformat()

    # Determine role and confidence
    if _matches_owner_identifiers(sender_ref, settings.owner_identifiers):
        role = "owner"
        confidence = settings.owner_auth_confidence
        name = sender_ref  # Will be overridden when entity link is made
    else:
        role = settings.default_external_role
        confidence = settings.default_auth_confidence
        # Try to extract a name from the sender_ref
        # For emails: use the local part; for plain names: use as-is
        if "@" in sender_ref:
            name = sender_ref.split("@")[0].replace(".", " ").replace("_", " ").title()
        else:
            name = sender_ref

    principal = graph.add_object(
        "principal",
        Principal(
            name=name,
            role=role,
            auth_confidence=confidence,
            identifiers={"ref": sender_ref},
            channel=channel,
            last_seen_at=now,
            frame_id=frame_id,
            metadata={"resolved_from_source": source_id},
        ).model_dump(),
    )

    # Create resolves_to relation: source → principal
    try:
        graph.add_relation("resolves_to", source_id, principal.id)
    except Exception:
        pass


@behavior(
    name="auth_context_builder",
    on=["object.created"],
    where={"object.type": "principal"},
    creates=["auth_context"],
)
def auth_context_builder(event, graph, ctx, *, settings: IdentitySettings):
    """Create an AuthContext for a resolved principal.

    On: object.created (principal)
    Creates: auth_context (if settings.create_auth_context is True)
    Creates: authenticated_by(principal → auth_context) relation

    The AuthContext snapshots the principal's role at creation time,
    so downstream behaviors can check role without re-fetching the principal.
    """
    if not settings.create_auth_context:
        return

    obj = event.payload.get("object", {})
    principal_id = obj.get("id")
    principal_data = obj.get("data", {})

    role = principal_data.get("role", "unknown")
    channel = principal_data.get("channel", "unknown") or "unknown"
    frame_id = principal_data.get("frame_id")

    now = datetime.now(timezone.utc).isoformat()

    auth_ctx = graph.add_object(
        "auth_context",
        AuthContext(
            principal_id=principal_id,
            principal_role=role,
            channel=channel,
            session_id=None,
            verified_at=now if role == "owner" else None,
            frame_id=frame_id,
            metadata={"created_by": "auth_context_builder"},
        ).model_dump(),
    )

    # Create authenticated_by relation: principal → auth_context
    try:
        graph.add_relation("authenticated_by", principal_id, auth_ctx.id)
    except Exception:
        pass


@behavior(
    name="permission_checker",
    on=["object.created"],
    where={"object.type": "action"},
    creates=[],
)
def permission_checker(event, graph, ctx, *, settings: IdentitySettings):
    """Check that the proposing principal has permission for an action.

    On: object.created (action, status=proposed)
    Creates: nothing — patches action.status to 'rejected' if denied
    Side effects: patches action.status + action.metadata.rejection_reason

    The action must carry principal_id in its metadata field.
    If no principal_id is present, the check is skipped (not rejected).

    Blocked principals always have their actions rejected.
    Unknown/external principals are checked against their role capabilities.
    """
    if not settings.check_permissions_on_proposed_actions:
        return

    obj = event.payload.get("object", {})
    action_id = obj.get("id")
    action_data = obj.get("data", {})

    if action_data.get("status") != "proposed":
        return

    principal_id = action_data.get("metadata", {}).get("principal_id", "")
    if not principal_id:
        return  # No principal context — skip check

    try:
        principal_obj = graph.get_object(principal_id)
    except Exception:
        return

    if not principal_obj:
        return

    principal_role = principal_obj.data.get("role", "unknown")
    action_kind = action_data.get("kind", "")
    risk_class = action_data.get("risk_class", "medium")

    # Blocked principals: always reject
    # Safe metadata expansion — handle None if schema had no default previously
    existing_meta: dict = action_data.get("metadata") or {}

    if principal_role == "blocked":
        try:
            graph.patch_object(action_id, {
                "status": "rejected",
                "metadata": {
                    **existing_meta,
                    "rejection_reason": "principal_blocked",
                    "checked_by": "permission_checker",
                },
            })
        except Exception:
            pass
        return

    # Build a Principal-like object to use .can() logic
    from .object_types import Principal as PrincipalModel
    p = PrincipalModel(name="", role=principal_role)

    # High/critical risk actions require owner or admin
    if risk_class in ("high", "critical") and principal_role not in ("owner", "admin"):
        try:
            graph.patch_object(action_id, {
                "status": "rejected",
                "metadata": {
                    **existing_meta,
                    "rejection_reason": f"risk_class_{risk_class}_requires_owner_or_admin",
                    "checked_by": "permission_checker",
                },
            })
        except Exception:
            pass
        return

    # Check execute capability for external/customer/unknown
    if action_kind in ("tool_call", "api_call", "external_write", "run_code"):
        if not p.can("execute") and principal_role not in ("owner", "admin", "collaborator"):
            try:
                graph.patch_object(action_id, {
                    "status": "rejected",
                    "metadata": {
                        **existing_meta,
                        "rejection_reason": "insufficient_role_for_execute",
                        "checked_by": "permission_checker",
                    },
                })
            except Exception:
                pass
            return

    # All other actions: mark permission as checked in metadata
    try:
        graph.patch_object(action_id, {
            "metadata": {
                **existing_meta,
                "permission_checked": True,
                "checked_by": "permission_checker",
                "principal_role": principal_role,
            },
        })
    except Exception:
        pass


BEHAVIORS = [principal_resolver, auth_context_builder, permission_checker]
