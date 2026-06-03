---
name: Principal dedup registry pattern
description: principal_resolver must deduplicate principals by sender_ref via local registry; always-create was a code review blocker
---

# Principal Dedup Registry Pattern

## The Rule
`principal_resolver` MUST check `_PRINCIPAL_REGISTRY` (normalized sender_ref → principal_id) before
creating a new Principal. On revisit: patch `last_seen_at` + increment `seen_count`, then create
`resolves_to` relation and return. Only on first encounter: create Principal + index in registry.

The `comm_message_principal_resolver` (fires on comm_message.created for Communication Pack) MUST
share the SAME `_PRINCIPAL_REGISTRY` dict so both source and comm_message paths converge on the
same Principal objects across channels.

## Why
The first implementation always created a new Principal per source. This broke identity continuity
(same sender gets different principal IDs across messages) and permission consistency (each action
checked against a fresh, unrelated Principal). Code review flagged this as a blocking issue.

## How to Apply
- `_PRINCIPAL_REGISTRY: dict[str, str]` — module-level in behaviors.py
- Key: `sender_ref.strip().lower()`
- Value: `principal_id` (graph object ID)
- `clear_principal_registry()` must be called in fixture teardown
- Setting `auto_deduplicate_principals=False` bypasses the registry for isolated testing
- Email sender_refs should also be stored in `principal.identifiers["email"]` for Entity Pack linking
