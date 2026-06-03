"""Secrets Pack tools — v0.1.

SecretsManager: resolves CredentialRef names to actual secret values
at runtime via environment variables.

SECURITY RULES:
- The resolved secret value is RETURNED to the caller, not stored
- It is NEVER written to the graph, events, logs, or artifacts
- The caller must use it immediately (e.g. as a header) and discard it
- Usage is recorded as a SecretUsageEvent (name only, not value)
"""

from __future__ import annotations

import os
from typing import Optional

from activegraph.packs import tool


# ------------------------------------------------------------------ raw function (callable directly)


def resolve_credential_fn(
    credential_name: str,
    env_prefix: str = "",
    behavior_name: Optional[str] = None,
) -> Optional[str]:
    """Look up a credential by name from environment variables.

    The returned value must be used immediately and not persisted.
    The name (not the value) is recorded in SecretUsageEvent separately.

    Args:
        credential_name: Name of the credential (used as env var key)
        env_prefix: Optional prefix prepended to the env var name
        behavior_name: Caller name for audit trail

    Returns:
        The secret value string, or None if not found.
    """
    env_key = f"{env_prefix}{credential_name}".upper()
    return os.environ.get(env_key)


# ------------------------------------------------------------------ tool wrapper (for pack registration)


@tool(
    name="resolve_credential",
    description=(
        "Resolve a CredentialRef name to its actual secret value from the environment. "
        "Returns the secret value (use immediately, do not store in graph or logs). "
        "Returns None if the credential is not found."
    ),
)
def resolve_credential(
    credential_name: str,
    env_prefix: str = "",
    behavior_name: Optional[str] = None,
) -> Optional[str]:
    """Registered tool wrapper — delegates to resolve_credential_fn."""
    return resolve_credential_fn(
        credential_name=credential_name,
        env_prefix=env_prefix,
        behavior_name=behavior_name,
    )


TOOLS = [resolve_credential]
