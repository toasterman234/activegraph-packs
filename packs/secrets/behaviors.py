"""Secrets Pack behaviors — v0.1.

One behavior covering credential usage auditing:

1. secret_usage_recorder — on credential_ref.created, records a
   SecretUsageEvent to track that a credential was registered.

The actual secret resolution happens in the SecretsManager tool
(secrets/tools.py), not in behaviors. Behaviors only handle
graph-visible tracking events.

Design rules:
- NEVER log, print, or record actual secret values
- Only record credential NAME, behavior name, timestamp
- Behaviors track registration/usage metadata only
"""

from __future__ import annotations

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
    Creates: secret_usage_event (records registration, not the secret)

    This creates an audit trail of which credentials are registered
    in the system and when. Actual resolution events are recorded
    by the SecretsManager tool, not this behavior.
    """
    if not settings.record_usage_events:
        return

    obj = event.payload.get("object", {})
    ref_data = obj.get("data", {})
    ref_name = ref_data.get("name", "")

    if not ref_name:
        return

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    graph.add_object(
        "secret_usage_event",
        SecretUsageEvent(
            credential_ref_name=ref_name,
            behavior_name="secret_usage_recorder",
            resolved=False,  # This is a registration event, not a resolution
            timestamp=now,
            metadata={"event_type": "registered"},
        ).model_dump(),
    )


BEHAVIORS = [secret_usage_recorder]
