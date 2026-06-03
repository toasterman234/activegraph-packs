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

## @behavior decorator signature

```python
@behavior(name, on, where, view, creates, budget, priority)
```

- NO `description` parameter — put description in the docstring.
- `on` is a list of event names, e.g. `["object.created"]`
- `where` is a dict filter, e.g. `{"object.type": "memory_candidate"}`
- Behaviors receive settings as `*, settings: MySettings` keyword-only arg when pack loads them.

**Why:** `@behavior` will raise TypeError if unknown kwargs are passed.

## load_prompts_from_dir must be guarded

```python
_PROMPTS_DIR = Path(__file__).parent / "prompts"
prompts=load_prompts_from_dir(_PROMPTS_DIR) if _PROMPTS_DIR.exists() else ()
```

**Why:** If the prompts/ dir doesn't exist, load_prompts_from_dir may fail or return nothing. Always guard with `.exists()`.
