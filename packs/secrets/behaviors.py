"""Secrets Pack behaviors — v0.1.

Two behaviors covering credential registration and resolution auditing:

1. secret_usage_recorder — on credential_ref.created, records a
   SecretUsageEvent (event_type='registered') to track registration.

2. credential_resolution_recorder — on secret_usage_event.created
   (resolved=True), patches CredentialRef.last_used_at and use_count
   to reflect actual resolution activity.

The actual secret resolution happens via resolve_credential_fn or
resolve_and_audit_fn. Behaviors handle graph-visible tracking only.

Design rules:
- NEVER log, print, or record actual secret values
- Only record credential NAME, behavior name, timestamp
- secret_usage_recorder handles registration events
- credential_resolution_recorder handles resolution events (resolved=True)
"""

from __future__ import annotations

from datetime import datetime, timezone

from activegraph.packs import behavior

from .object_types import SecretUsageEvent
from .settings import SecretsSettings


@behavior(
    name="secret_usage_recorder",
    on=["object.created"],
    where={"object.type": "credential_ref"},
    creates=["secret_usage_event"],
)
def secret_usage_recorder(event, graph, ctx, *, settings: SecretsSettings):
    """Record a SecretUsageEvent when a CredentialRef is registered.

    On: object.created (credential_ref)
    Creates: secret_usage_event (event_type=registered)

    This creates an audit trail of which credentials are registered
    in the system and when.
    """
    if not settings.record_usage_events:
        return

    obj = event.payload.get("object", {})
    ref_data = obj.get("data", {})
    ref_name = ref_data.get("name", "")

    if not ref_name:
        return

    now = datetime.now(timezone.utc).isoformat()

    graph.add_object(
        "secret_usage_event",
        SecretUsageEvent(
            credential_ref_name=ref_name,
            behavior_name="secret_usage_recorder",
            resolved=False,
            timestamp=now,
            metadata={"event_type": "registered"},
        ).model_dump(),
    )


@behavior(
    name="credential_resolution_recorder",
    on=["object.created"],
    where={"object.type": "secret_usage_event"},
    creates=[],
)
def credential_resolution_recorder(event, graph, ctx, *, settings: SecretsSettings):
    """Update CredentialRef stats when a resolution usage event is created.

    On: object.created (secret_usage_event, resolved=True)
    Creates: nothing (patches existing credential_ref objects)
    Side effects: patches credential_ref.last_used_at and use_count

    This fires whenever a SecretUsageEvent with resolved=True is added
    to the graph — typically created by resolve_and_audit_fn after
    successfully resolving a credential at call time.
    """
    obj = event.payload.get("object", {})
    event_data = obj.get("data", {})

    # Only process resolution attempt events (event_type='resolved')
    # NOT registration events (event_type='registered')
    event_type = event_data.get("metadata", {}).get("event_type", "")
    if event_type != "resolved":
        return

    ref_name = event_data.get("credential_ref_name", "")
    if not ref_name:
        return

    now = datetime.now(timezone.utc).isoformat()

    # Use the credential_ref_id from metadata for a direct get_object() lookup.
    # Behaviors must NOT call graph.objects() — only add_object, add_relation,
    # get_object, and patch_object are safe inside behavior context.
    credential_ref_id = event_data.get("metadata", {}).get("credential_ref_id", "")
    if not credential_ref_id:
        return

    try:
        ref_obj = graph.get_object(credential_ref_id)
    except Exception:
        return

    if not ref_obj:
        return

    current_count = ref_obj.data.get("use_count", 0)
    try:
        graph.patch_object(credential_ref_id, {
            "last_used_at": now,
            "use_count": current_count + 1,
        })
    except Exception:
        pass


BEHAVIORS = [secret_usage_recorder, credential_resolution_recorder]
