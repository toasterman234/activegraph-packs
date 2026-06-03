# Secrets Pack v0.1

> Credential reference management. Secrets never enter model context.

## Overview

Secrets Pack provides a safe way to reference credentials without exposing them in the graph, events, behaviors, or artifacts.

**Critical invariant:** Actual secret values are NEVER stored in graph objects, events, or logs. `CredentialRef` contains a **name only**. The actual secret is resolved from environment variables at execution time by the `resolve_credential` tool.

## Behavior Map

```
credential_ref.created
  → secret_usage_recorder
      creates secret_usage_event (name only, not value)
      [records credential registration for audit trail]
```

## Object Types

| Type | Description | Key Fields |
|------|-------------|------------|
| `credential_ref` | Reference to a credential — name only, never the secret | `name`, `scope`, `provider_hint`, `last_used_at`, `use_count`, `enabled` |
| `secret_usage_event` | Audit record of credential resolution | `credential_ref_name`, `behavior_name`, `resolved`, `timestamp` |

## Relation Types

| Relation | Source → Target | Description |
|----------|-----------------|-------------|
| `credential_used_in` | secret_usage_event → capability_call | Associates a usage event with the call that triggered it |

## Dependencies

```python
requires = ["core"]
integrates_with = ["tool_gateway"]
```

## Security Design

```
┌──────────────────────────────────────────────────────────┐
│  NEVER in graph / events / logs:                         │
│    ❌ actual API key value                                │
│    ❌ token string                                        │
│    ❌ password                                            │
│                                                          │
│  OK in graph / events / logs:                            │
│    ✅ credential NAME ("OPENAI_API_KEY")                  │
│    ✅ scope ("read", "write")                             │
│    ✅ provider_hint ("openai")                            │
│    ✅ usage timestamp                                     │
│    ✅ resolved: True/False                                │
└──────────────────────────────────────────────────────────┘
```

## Usage

```python
import os
from activegraph import Runtime, Graph
from packs.core import pack as core_pack
from packs.secrets import pack as secrets_pack, SecretsSettings
from packs.secrets.tools import resolve_credential

# Set the secret in environment (never in code)
os.environ["OPENAI_API_KEY"] = "sk-..."  # in production, set externally

# Load packs
rt = Runtime(Graph())
rt.load_pack(core_pack)
rt.load_pack(secrets_pack, settings=SecretsSettings())

# Register a credential reference (safe — no secret stored)
rt.graph.add_object("credential_ref", {
    "name": "OPENAI_API_KEY",
    "scope": "write",
    "provider_hint": "openai",
})
rt.run_until_idle()  # secret_usage_recorder fires → SecretUsageEvent created

# Resolve the actual secret at call time (use immediately, do not store)
api_key = resolve_credential("OPENAI_API_KEY")
if api_key:
    # Use api_key here, then let it go out of scope
    pass
```

## Settings

| Field | Default | Description |
|-------|---------|-------------|
| `env_prefix` | `""` | Prefix prepended to credential names for env var lookup |
| `record_usage_events` | `True` | Create SecretUsageEvent for each registration/resolution |
| `fail_on_missing` | `False` | Raise ValueError if credential not found in env |

## Fixtures

```bash
python packs/secrets/fixtures/run_fixtures.py
```

## CHANGELOG

See [`CHANGELOG.md`](CHANGELOG.md).
