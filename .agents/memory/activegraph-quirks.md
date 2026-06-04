---
name: ActiveGraph API quirks
description: Non-obvious ActiveGraph runtime/pack API behaviors that bite when writing packs or behaviors.
---

# add_relation argument order differs per pack

`graph.add_relation(...)` positional order is NOT consistent across packs in this
repo:

- **memory_gateway** behaviors call it as `(type, source, target)`.
- **chat** behaviors call it as `(source, target, type)`.

**Why:** the underlying API accepts these positionally and the two packs were
written with different conventions; passing the wrong order silently builds a
backwards/garbage edge instead of erroring.

**How to apply:** when adding a relation inside a behavior, copy the order from a
NEARBY existing `add_relation` call in the SAME pack rather than assuming a global
convention. Prefer keyword args when the signature allows it.

# Behavior registration order IS execution order

The `BEHAVIORS = [...]` list order is the order behaviors run. Any behavior that
must produce a `*_context` object the LLM responder folds into its prompt (e.g.
chat ChatContext / ProfileContextView / MemoryContext) MUST be listed BEFORE the
responder, or the context arrives a turn too late.

## UI logs are derived client-side from /trace
The api-server only proxies whole-collection GETs (/trace, /graph, /packs, /frames, /summary). There are NO per-object or per-behavior log endpoints. Any "logs for object X" or "logs for behavior Y" UI must fetch /trace and filter client-side by `object_id` / `behavior_name`. /trace is windowed (default limit 200, demo caps via `limit` param) so such views show only the latest N events, not full history — label them accordingly.

## Mockup preview screenshots
- `screenshot type=external_url` against a mockup-sandbox `/__mockup/preview/...` URL can capture a blank white page (it does not reliably wait for client-side React render).
- Use `screenshot type=app_preview` with `artifact_dir_name="mockup-sandbox"` and `path="/preview/{folder}/{Component}"` — it waits for mount and returns browser logs. (Resolves to localhost:80/__mockup/preview/...)
