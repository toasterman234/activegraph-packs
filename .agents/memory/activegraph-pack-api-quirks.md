---
name: ActiveGraph Pack API Quirks
description: Key non-obvious constraints when building activegraph packs — Pack constructor, tool callability, behavior decorator signature.
---

## Pack constructor accepted params (v1.0.5.post2)

```python
Pack(name, version, description, object_types, relation_types,
     behaviors, tools, policies, prompts, settings_schema)
```

- `requires` and `integrates_with` are NOT accepted kwargs — put them in comments/docstrings.
- `policies` and `prompts` should be `()` (empty tuple), not `[]`, to be consistent with other tuple fields.

**Why:** TypeError on load if unsupported kwargs are passed. Only discovered by runtime check, not by type hints.

## @tool decorated objects are NOT callable

`@tool(name=..., description=...)` returns a `Tool` dataclass — NOT a callable function.

```python
# WRONG — Tool object is not callable
result = execute_capability(...)

# RIGHT — use the raw underlying function
result = execute_capability_fn(...)
# OR
result = execute_capability.fn(...)
```

**How to apply:** Always expose the raw function separately (`execute_capability_fn`) and wrap it with `@tool` for pack registration. The `@tool` wrapper's `.fn` attribute also works but raw export is cleaner.

## graph.objects() is NOT safe inside behaviors

Inside a behavior, only these graph methods are safe:
- `graph.add_object(type, data)` ✅
- `graph.add_relation(type, source, target)` ✅
- `graph.get_object(id)` ✅
- `graph.patch_object(id, patch)` ✅

**NEVER** call `graph.objects()` or `graph.objects(type=...)` inside a behavior — it raises `AttributeError` silently (behavior fails with `reason=exception.AttributeError`).

**How to apply:** When a behavior needs to look up an existing object, pass the object's ID through the triggering event's data or metadata, then use `graph.get_object(id)` directly. For example, Secrets pack passes `credential_ref_id` in the SecretUsageEvent metadata so `credential_resolution_recorder` can use `get_object()` instead of scanning all objects.

## @behavior decorator signature

```python
@behavior(name, on, where, view, creates, budget, priority)
```

- NO `description` parameter — put description in the docstring.
- `on` is a list of event names, e.g. `["object.created"]`
- `where` is a dict filter, e.g. `{"object.type": "memory_candidate"}`
- Behaviors receive settings as `*, settings: MySettings` keyword-only arg when pack loads them.

**Why:** `@behavior` will raise TypeError if unknown kwargs are passed.

## Cross-pack credential injection pattern

To wire Secrets into Tool Gateway execution without violating the "no graph.objects() in behaviors" rule:

1. `CapabilityCall` carries both `credential_ref_name` AND `credential_ref_id`
2. `policy_enforcer` copies both fields into `CapabilityApproval`
3. `call_executor` reads them from the approval, calls `resolve_and_audit_fn(credential_ref_id=...)`, discards the secret after use
4. `credential_resolution_recorder` updates `last_used_at`/`use_count` via `get_object(credential_ref_id)`

**Why:** The secret value must never be stored in the graph. The ID is safe to pass through because it's a graph object reference, not the secret itself. use_count after a call with credential_ref_id set should be ≥ 2 (one manual + one call_executor injection).

## patch_object does NOT re-trigger behaviors

`graph.patch_object(id, patch)` is silent — it does NOT emit a new `object.created` event. If a behavior is meant to fire on a status change, the object must be CREATED with the target status. Fixtures testing status-change-triggered behaviors must create the object with the desired status directly rather than creating + patching.

**Why:** The response_dispatcher behavior fires on `object.created` where status=approved. A fixture that created a "proposed" candidate and then patched to "approved" never triggered the dispatcher.

## Pydantic model_config field name conflict

Never name a `BaseModel` field `model_config` — it conflicts with Pydantic v2's internal `model_config` class variable and causes `TypeError: 'FieldInfo' object is not iterable` at import time. Rename to `llm_config` or similar.

## load_prompts_from_dir must be guarded

```python
_PROMPTS_DIR = Path(__file__).parent / "prompts"
prompts=load_prompts_from_dir(_PROMPTS_DIR) if _PROMPTS_DIR.exists() else ()
```

**Why:** If the prompts/ dir doesn't exist, load_prompts_from_dir may fail or return nothing. Always guard with `.exists()`.
