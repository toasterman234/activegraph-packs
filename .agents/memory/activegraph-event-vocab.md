---
name: ActiveGraph event vocabulary & payload shapes
description: Non-obvious trace event types and payload fields for the ActiveGraph Inspector UI; the demo run only exercises a subset.
---

# ActiveGraph trace events (for the Inspector UI)

Source of truth: `activegraph/trace/printer.py` (formatters) and `activegraph/core/graph.py` (emission).

**Top-level event fields are sparse.** On most trace events `event.pack`, `event.behavior_name`, and `event.object_type` are NULL. The behavior name lives in `event.payload.behavior`, not the top-level column. Filtering/displaying by top-level `pack`/`behavior_name` is mostly useless — read the payload.

**Patches are three distinct event types, not one with a status field:**
- `patch.applied` — payload `{ patch }`, where patch = `{ id, target, op, value(dict of new field values), expected_version, proposed_by, status, ... }`. No before/after — only new values. Do NOT fabricate a diff.
- `patch.proposed` — payload `{ patch }`.
- `patch.rejected` — payload `{ patch_id, target, reason, current_version }` (flat, NOT nested under `patch`, and NOT a rejected-status `patch.applied`). Rejected patches belong on a Failures view.

**Other types:** `relation.created` (payload.relation.id == event.object_id, use for created-time join with /graph relations), `object.created`, `behavior.started/completed`, `behavior.failed` (payload `{ behavior, exception_type, message, reason? }`), `tool.requested`/`tool.responded` (payload `{ behavior, tool, args_hash, cache_hit, deterministic, latency_seconds, cost_usd, error?{reason,message} }`), `llm.requested/responded` (model/tokens/cost/latency/cache_hit), `pack.loaded`, `runtime.idle`, `pattern.matched`, `behavior.scheduled`.

**Why this matters:** the framework supports the full vocabulary (tools, failures) but a deterministic demo pack emits none of `tool.*` or `behavior.failed` — so Tools/Failures inspector pages render honest empty states in the demo yet populate in real runs. Build them anyway; don't assume "no data == feature unsupported."

**Docs concepts** (docs.activegraph.ai/concepts/<slug>/, CORS `*`, extract `<article>`): existing slugs include relations, patches, failure-model, events, behaviors, graph, frames, patterns, policies, replay, type-system, views, forking. There is NO `tools` concept page — Tools must use an inline static explanation / fall back to the concepts index.
