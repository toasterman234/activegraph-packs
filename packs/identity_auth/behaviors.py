"""Identity/Auth Pack behaviors — v0.1.

Four behaviors covering the full identity lifecycle:

1. principal_resolver — on source.created, extracts sender_ref and resolves
   it to a Principal. Reuses existing principals from the local registry by
   normalized sender_ref (dedup). Assigns role 'owner' if sender_ref matches
   any owner_identifier; otherwise assigns default_external_role.

2. comm_message_principal_resolver — same logic as principal_resolver but
   fires on comm_message.created (Communication Pack). Shares the registry
   so both paths converge on the same Principal objects.

3. auth_context_builder — on principal.created, creates an AuthContext
   that scopes the session for downstream behaviors.

4. permission_checker — on action.created (status=proposed), validates
   that the proposing principal's role allows the action. Rejects
   actions from blocked principals or those lacking required capabilities.

Design rules:
- Behaviors must NOT call graph.objects() — only add_object, add_relation,
  get_object, patch_object are safe in behavior context
- Principals never store passwords, tokens, or actual secrets
- Permission checks use role hierarchy (Principal.can(action))
- principal_id must be in action.metadata for permission_checker to fire
- _PRINCIPAL_REGISTRY tracks normalized sender_ref → principal_id for dedup;
  clear between tests with clear_principal_registry()
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from activegraph.packs import behavior

from .object_types import AuthContext, Principal
from .settings import IdentitySettings


# ------------------------------------------------------------------ local registry
# Maps normalized sender_ref → principal_id so principal_resolver can reuse
# existing principals across multiple sources from the same sender.

_PRINCIPAL_REGISTRY: dict[str, str] = {}  # normalized_sender_ref → principal_id


def _normalize_identifier(s: str) -> str:
    return s.strip().lower()


def clear_principal_registry() -> None:
    """Clear the local principal registry. Used in fixture teardown."""
    _PRINCIPAL_REGISTRY.clear()


# ------------------------------------------------------------------ helpers


def _matches_owner_identifiers(sender_ref: str, owner_identifiers: list[str]) -> bool:
    """Check if sender_ref matches any owner identifier (case-insensitive)."""
    norm = _normalize_identifier(sender_ref)
    return any(_normalize_identifier(oid) == norm for oid in owner_identifiers)


def _extract_display_name(sender_ref: str) -> str:
    """Best-effort display name from a sender_ref string."""
    if "@" in sender_ref:
        return sender_ref.split("@")[0].replace(".", " ").replace("_", " ").title()
    return sender_ref


# ------------------------------------------------------------------ shared resolution logic


def _resolve_principal(
    sender_ref: str,
    channel: str,
    frame_id: Optional[str],
    source_id: str,
    graph,
    settings: IdentitySettings,
) -> Optional[str]:
    """Core principal resolution logic shared by source and comm_message paths.

    Returns the principal_id (either existing or newly created).
    Creates resolves_to(source_or_message → principal) relation.
    """
    now = datetime.now(timezone.utc).isoformat()
    norm_ref = _normalize_identifier(sender_ref)

    # --- Dedup: check if we already resolved this sender ---
    if settings.auto_deduplicate_principals and norm_ref in _PRINCIPAL_REGISTRY:
        existing_id = _PRINCIPAL_REGISTRY[norm_ref]
        # Patch last_seen_at and bump seen_count on existing principal
        try:
            existing = graph.get_object(existing_id)
            if existing:
                current_count = existing.data.get("seen_count", 1)
                graph.patch_object(existing_id, {
                    "last_seen_at": now,
                    "seen_count": current_count + 1,
                })
        except Exception:
            pass

        # Still create the resolves_to relation from this new source
        try:
            graph.add_relation("resolves_to", source_id, existing_id)
        except Exception:
            pass

        return existing_id

    # --- New sender: determine role and confidence ---
    if _matches_owner_identifiers(sender_ref, settings.owner_identifiers):
        role = "owner"
        confidence = settings.owner_auth_confidence
        name = sender_ref
    else:
        role = settings.default_external_role
        confidence = settings.default_auth_confidence
        name = _extract_display_name(sender_ref)

    identifiers: dict[str, str] = {"ref": sender_ref}
    if "@" in sender_ref:
        identifiers["email"] = sender_ref  # enable entity-backed lookup later

    principal = graph.add_object(
        "principal",
        Principal(
            name=name,
            role=role,
            auth_confidence=confidence,
            identifiers=identifiers,
            channel=channel,
            last_seen_at=now,
            seen_count=1,
            frame_id=frame_id,
            metadata={"resolved_from_source": source_id},
        ).model_dump(),
    )

    # Index in local registry for future dedup
    if settings.auto_deduplicate_principals:
        _PRINCIPAL_REGISTRY[norm_ref] = principal.id

    # Create resolves_to relation: source → principal
    try:
        graph.add_relation("resolves_to", source_id, principal.id)
    except Exception:
        pass

    return principal.id


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
    Creates: principal (on first encounter) OR patches existing (on revisit)
    Creates: resolves_to(source → principal) relation

    Dedup: normalized sender_ref is checked against _PRINCIPAL_REGISTRY.
    If found, patches last_seen_at + increments seen_count on the existing
    Principal. Otherwise creates a new Principal and indexes it.

    Role assignment:
    - Matches owner_identifiers → role='owner', owner_auth_confidence
    - Otherwise → default_external_role, default_auth_confidence

    Stores email as an identifier so Entity Pack can link Principal to Entity.
    """
    obj = event.payload.get("object", {})
    source_id = obj.get("id")
    source_data = obj.get("data", {})

    sender_ref = source_data.get("sender_ref", "")
    if not sender_ref:
        return

    channel = source_data.get("channel", "unknown")
    frame_id = source_data.get("frame_id")

    _resolve_principal(sender_ref, channel, frame_id, source_id, graph, settings)


@behavior(
    name="comm_message_principal_resolver",
    on=["object.created"],
    where={"object.type": "comm_message"},
    creates=["principal"],
)
def comm_message_principal_resolver(event, graph, ctx, *, settings: IdentitySettings):
    """Resolve a CommMessage's sender to a Principal.

    On: object.created (comm_message) — Communication Pack
    Creates: principal (on first encounter) OR patches existing (on revisit)
    Creates: resolves_to(comm_message → principal) relation

    Mirrors principal_resolver but consumes CommMessage objects.
    Shares _PRINCIPAL_REGISTRY so both triggers converge on the same Principals.
    """
    obj = event.payload.get("object", {})
    msg_id = obj.get("id")
    msg_data = obj.get("data", {})

    sender_ref = msg_data.get("sender_ref", "") or msg_data.get("from_address", "")
    if not sender_ref:
        return

    channel = msg_data.get("channel", "unknown")
    frame_id = msg_data.get("frame_id")

    _resolve_principal(sender_ref, channel, frame_id, msg_id, graph, settings)


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

    Only fires on NEW principals (not on revisit patches). The event carries
    the object data as it was at creation time, not after patches.
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

    # Safe metadata access — handle None if metadata wasn't set
    existing_meta: dict = action_data.get("metadata") or {}
    principal_id = existing_meta.get("principal_id", "")
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
    p = Principal(name="", role=principal_role)

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


BEHAVIORS = [
    principal_resolver,
    comm_message_principal_resolver,
    auth_context_builder,
    permission_checker,
]
