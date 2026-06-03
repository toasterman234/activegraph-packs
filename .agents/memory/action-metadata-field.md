---
name: Action metadata field
description: Core Pack's Action schema did not have a metadata field; permission_checker behavior silently failed when trying to patch metadata onto actions
---

# Action metadata field

## The Rule
Core Pack's `Action` model must include `metadata: dict[str, Any] = Field(default_factory=dict)`.
The `permission_checker` behavior in Identity Pack reads `action_data.get("metadata") or {}` 
and writes back `{"permission_checked": True, ...}` or `{"rejection_reason": "..."}`.

## Why
When `permission_checker` tried to do `**action_data.get("metadata", {})` and metadata was 
absent from the schema, the field returned `None` (key present with None value beats the default).
`**None` raises `TypeError` inside the behavior, which was caught by `except Exception: pass`, 
causing silent no-op. The action status was never patched to "rejected" or "permission_checked".

## How to Apply
- Core Pack: `packs/core/object_types.py` — `Action` model must have `metadata` field
- Behavior patch calls: always use `action_data.get("metadata") or {}` (not `.get("metadata", {})`) 
  to defend against `None` even if the schema has the field
- Other packs adding behavior fields to Core objects: check the Core schema first for the target field
